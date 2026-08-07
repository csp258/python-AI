"""
Vector-based document retrieval and context formatting for the LLM prompt.

Provides pure vector search (used as building block by the hybrid retriever)
and a utility for formatting retrieved chunks into a citation-friendly context
block with source tracking.
"""

from typing import List, Tuple

from langchain_core.documents import Document

from config import settings
from rag.vectorstore import get_vector_store


def _deduplicate(docs: List[Document]) -> List[Document]:
    """
    Remove near-duplicate documents by comparing the first 200 characters of
    each document's content. This prevents the same chunk from appearing
    multiple times in the results.
    """
    seen = set()
    result = []
    for doc in docs:
        key = doc.page_content[:200]
        if key not in seen:
            seen.add(key)
            result.append(doc)
    return result


def retrieve(query: str, top_k: int = None) -> Tuple[List[Document], List[float]]:
    """
    Perform pure vector similarity search and filter results by a minimum
    relevance score threshold (0.3). Documents below this threshold are
    considered too dissimilar to be useful.

    Returns (documents, scores) or empty lists if nothing meets the threshold.
    """
    if top_k is None:
        top_k = settings.top_k
    store = get_vector_store()

    docs_with_scores = store.similarity_search_with_relevance_scores(query, k=top_k)
    docs = [doc for doc, _score in docs_with_scores]
    scores = [score for _doc, score in docs_with_scores]

    # Filter out low-relevance results to avoid confusing the LLM with unrelated content
    filtered_docs = []
    filtered_scores = []
    for doc, score in zip(docs, scores):
        if score >= 0.3:
            filtered_docs.append(doc)
            filtered_scores.append(score)

    if not filtered_docs:
        return [], []

    return filtered_docs, filtered_scores


def format_context(docs: List[Document], scores: List[float]) -> Tuple[str, List[dict]]:
    """
    Format retrieved documents into a structured context string for the LLM
    prompt and a parallel sources list for the API response.

    The context string uses numbered citation markers like 【参考资料1】 that the
    system prompt instructs the LLM to reference in its answer.
    The sources list records filename, preview text, and relevance score for
    storage and frontend display.
    """
    context_parts = []
    sources = []
    for i, (doc, score) in enumerate(zip(docs, scores), 1):
        filename = doc.metadata.get("source", "未知文档")
        context_parts.append(f"【参考资料{i} 来源:{filename} 相似度:{score:.2f}】\n{doc.page_content}")
        sources.append({
            "filename": filename,
            "content": doc.page_content[:500],
            "score": round(score, 4),
        })

    return "\n\n".join(context_parts), sources
