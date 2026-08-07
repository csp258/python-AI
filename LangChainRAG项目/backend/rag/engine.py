"""
RAG engine: orchestrates document indexing, hybrid retrieval, and answer generation.

This module ties together all RAG pipeline stages: loading and chunking documents,
storing embeddings in ChromaDB, performing hybrid (vector + BM25) retrieval with
RRF fusion, and streaming LLM-generated answers with source citations.
"""

import os
import hashlib
import logging
from typing import AsyncIterator, Tuple, List

from langchain_core.documents import Document as LCDocument

from config import settings
from database import SessionLocal
from models import Document, Message
from rag.loader import load_document
from rag.splitter import get_splitter
from rag.vectorstore import get_vector_store, reset_vector_store
from rag.retriever import format_context
from rag.hybrid_retriever import hybrid_retriever
from rag.generator import generate_stream
from rag.faq_cache import try_faq
from rag.intent import classify_intent

logger = logging.getLogger(__name__)


def index_document(doc_id: int, file_path: str, ext: str) -> int:
    """
    Load a document file, split it into chunks, and store embeddings in the
    vector database. Each chunk is tagged with metadata (document ID, source
    filename, and a unique chunk ID) so it can be traced back later.

    Returns the number of chunks created, or 0 if the document produced no
    chunkable text.
    """
    raw_docs = load_document(file_path, ext)
    splitter = get_splitter()
    chunks = splitter.split_documents(raw_docs)

    if not chunks:
        return 0

    # Enrich every chunk with tracking metadata for provenance and deletion
    for chunk in chunks:
        chunk.metadata["document_id"] = str(doc_id)
        chunk.metadata["source"] = os.path.basename(file_path)
        # Use a truncated MD5 hash as a short, deterministic chunk identifier
        content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()[:12]
        chunk.metadata["chunk_id"] = f"{doc_id}_{content_hash}"

    store = get_vector_store()
    store.add_documents(chunks)
    # Invalidate the BM25 cache so the next search rebuilds it with the new chunks
    hybrid_retriever.mark_dirty()
    return len(chunks)


def remove_document(doc_id: int, filename: str):
    """
    Remove all chunks belonging to a document from ChromaDB. After deletion
    the hybrid retriever cache is invalidated so stale BM25 entries are not
    returned by future searches.
    """
    store = get_vector_store()
    try:
        results = store.get(where={"document_id": str(doc_id)})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            store.delete(ids=ids_to_delete)
    except Exception as e:
        # Log the error for debugging; the file-on-disk deletion is handled by the caller
        logger.warning("Failed to remove chunks for doc_id=%d from vector store: %s", doc_id, e)
    hybrid_retriever.mark_dirty()


def get_document_chunks(doc_id: int) -> dict:
    """
    Retrieve chunk previews for a given document from the vector store.
    Each preview truncates the chunk text to the first 300 characters to
    keep the response lightweight (admin UI preview).
    """
    store = get_vector_store()
    try:
        results = store.get(where={"document_id": str(doc_id)})
        chunks = []
        for i, (doc_text, meta) in enumerate(zip(
            results.get("documents", []),
            results.get("metadatas", []),
        )):
            chunks.append({
                "index": i + 1,
                "content": doc_text[:300],
                "metadata": meta,
            })
        return {"total": len(chunks), "chunks": chunks}
    except Exception as e:
        logger.error("Failed to get chunks for doc_id=%d: %s", doc_id, e)
        return {"total": 0, "chunks": []}


def _build_history_text(messages: List[Message]) -> str:
    """
    Build a condensed chat-history text from the last 10 messages for use
    as context in the LLM prompt. Each message is truncated to 200 characters
    to keep the prompt compact.
    """
    if not messages:
        return ""
    history_parts = []
    # Take last 10 messages, excluding the most recent user message
    # (which will be the current question and is passed separately)
    for msg in messages[-10:-1]:
        role = "用户" if msg.role == "user" else "助手"
        history_parts.append(f"{role}: {msg.content[:200]}")
    return "\n".join(history_parts)


async def query_stream(
    question: str,
    history: List[Message],
) -> AsyncIterator[Tuple[str, List[dict]]]:
    """
    Full RAG query pipeline executed as an async generator so the frontend
    receives answer tokens in real time (SSE streaming).

    Pipeline stages:
    1. FAQ cache check — answers high-frequency questions instantly
    2. Intent recognition — classifies the question for analytics
    3. Hybrid retrieval — searches vector + BM25, fused via RRF
    4. LLM generation — streams the answer token-by-token

    The final yielded tuple contains an empty string and the source list,
    which the chat endpoint uses to persist source citations.
    """
    # Step 1: Try FAQ cache for high-frequency e-commerce questions
    faq_result = try_faq(question)
    if faq_result:
        answer, sources = faq_result
        yield (answer, sources)
        return

    # Step 2: Intent recognition — currently used for logging/analytics only
    intent = classify_intent(question)

    # Step 3: Hybrid retrieval combining dense vector search with sparse BM25 keywords
    docs, scores = hybrid_retriever.search(question)

    if not docs:
        yield ("抱歉，知识库中暂时没有与您问题相关的信息。请尝试换个方式提问，或联系管理员补充相关知识库内容。", [])
        return

    # Format retrieved chunks into a single prompt context block with numbered citations
    context, sources = format_context(docs, scores)

    # Step 4: Stream the LLM-generated answer back to the client
    async for chunk, _ in generate_stream(context, question):
        if chunk:
            yield (chunk, [])

    # Final yield carries source citations for persistence in the database
    yield ("", sources)


# ---------------------------------------------------------------------------
# Module-level singleton: provides a unified API surface for all RAG operations.
# Imported as ``rag_engine`` by routers and other consumers.
# Using a lightweight anonymous class to avoid the overhead of a full class
# definition while still keeping state (e.g., lazy-loaded ChromaDB client).
# ---------------------------------------------------------------------------
rag_engine = type("RAGEngine", (), {
    "index_document": staticmethod(index_document),
    "remove_document": staticmethod(remove_document),
    "get_document_chunks": staticmethod(get_document_chunks),
    "query_stream": staticmethod(query_stream),
})()
