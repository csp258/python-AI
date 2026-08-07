"""Hybrid retrieval: vector search + BM25 keyword search with RRF fusion."""
import logging
from typing import List, Tuple
from rank_bm25 import BM25Okapi
import jieba

from langchain_core.documents import Document as LCDocument

from config import settings
from rag.vectorstore import get_vector_store

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines dense vector search (ChromaDB embeddings) with sparse keyword
    search (BM25 via jieba tokenization) using Reciprocal Rank Fusion (RRF).

    Why hybrid? Vector search captures semantic similarity but can miss exact
    keyword matches (e.g., product model numbers). BM25 excels at keyword
    matching but lacks semantic understanding. RRF merges both ranked lists
    into a single result set, giving users the best of both worlds.

    The BM25 index is lazily built and cached; call ``mark_dirty()`` after
    adding or removing documents from the vector store to trigger a rebuild.
    """

    def __init__(self):
        self._bm25: BM25Okapi | None = None
        self._bm25_docs: List[LCDocument] = []
        self._dirty = True

    def mark_dirty(self):
        """Mark the BM25 cache as stale so the next search rebuilds it."""
        self._dirty = True

    def _ensure_bm25(self):
        """
        Rebuild the BM25 index from all documents currently in the vector store,
        but only if the cache is stale. Uses jieba for Chinese word segmentation
        since the knowledge base is primarily Chinese e-commerce content.
        """
        if not self._dirty and self._bm25 is not None:
            return

        store = get_vector_store()
        try:
            results = store.get(include=["documents", "metadatas"])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            self._bm25_docs = [
                LCDocument(page_content=text, metadata=meta or {})
                for text, meta in zip(documents, metadatas)
            ]

            if self._bm25_docs:
                # Tokenize with jieba (Chinese text segmentation) before building BM25
                tokenized = [list(jieba.cut(doc.page_content)) for doc in self._bm25_docs]
                self._bm25 = BM25Okapi(tokenized)
            else:
                self._bm25 = None
        except Exception as e:
            # Fall back to vector-only search if BM25 index construction fails
            logger.warning("Failed to build BM25 index: %s", e)
            self._bm25 = None
            self._bm25_docs = []

        self._dirty = False

    def search(
        self, query: str, top_k: int = None
    ) -> Tuple[List[LCDocument], List[float]]:
        """
        Perform hybrid search and return the top-k results with fused scores.

        The process:
        1. Vector search: retrieve 2*top_k candidates from ChromaDB
        2. BM25 search: retrieve top_k keyword matches from the cached index
        3. RRF fusion: combine both ranked lists into a single ranking by
           summing 1/(k + rank) for each result, where k=60 dampens the
           effect of high rankings
        4. Return the top_k results sorted by the fused RRF score
        """
        if top_k is None:
            top_k = settings.top_k

        store = get_vector_store()

        # --- Phase 1: Dense vector (semantic) retrieval ---
        # Fetch 2x candidates to give the fusion step more options to re-rank
        vec_results = store.similarity_search_with_relevance_scores(query, k=top_k * 2)
        vec_docs = [doc for doc, _ in vec_results]
        vec_scores = [score for _, score in vec_results]

        # --- Phase 2: Sparse keyword (BM25) retrieval ---
        self._ensure_bm25()
        bm25_docs = []
        bm25_scores = []
        if self._bm25 is not None:
            tokenized_query = list(jieba.cut(query))
            bm25_raw_scores = self._bm25.get_scores(tokenized_query)
            # Sort BM25 scores descending and take top_k positive-scoring results
            indexed = list(enumerate(bm25_raw_scores))
            indexed.sort(key=lambda x: x[1], reverse=True)
            for idx, score in indexed[:top_k]:
                if score > 0:
                    bm25_docs.append(self._bm25_docs[idx])
                    bm25_scores.append(score)

        # --- Phase 3: Reciprocal Rank Fusion (RRF) ---
        # Key insight: RRF does not require score normalization between the two
        # ranking methods. It simply sums 1/(k + rank) for each document across
        # both ranked lists. The constant k=60 is a widely-used default that
        # reduces the influence of very highly ranked single-source results.
        rrf_scores = {}
        doc_map = {}  # key -> (original_doc, original_score) for deduplication

        # Add vector search ranks to the RRF pool
        for rank, (doc, score) in enumerate(zip(vec_docs, vec_scores)):
            key = doc.page_content[:200]  # first 200 chars as dedup key
            rrf_scores[key] = rrf_scores.get(key, 0) + 1.0 / (60 + rank)
            doc_map[key] = (doc, score)

        # Add BM25 ranks (only add to doc_map if this is a new document)
        for rank, (doc, score) in enumerate(zip(bm25_docs, bm25_scores)):
            key = doc.page_content[:200]
            rrf_scores[key] = rrf_scores.get(key, 0) + 1.0 / (60 + rank)
            if key not in doc_map:
                # Normalize BM25 score to [0, 1] range for display purposes
                norm_score = score / max(bm25_scores) if max(bm25_scores, default=0) > 0 else 0.0
                doc_map[key] = (doc, norm_score)

        # --- Phase 4: Sort by fused RRF score and return top_k ---
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        final_docs = []
        final_scores = []
        for key, rrf in sorted_items:
            doc, _ = doc_map[key]
            final_docs.append(doc)
            final_scores.append(rrf)

        return final_docs, final_scores


# Module-level singleton instance
hybrid_retriever = HybridRetriever()
