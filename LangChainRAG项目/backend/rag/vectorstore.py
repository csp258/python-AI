"""
Vector store management: lazy-initialized ChromaDB with local Chinese embeddings.

Uses module-level globals to cache the embedding model and vector store
instances so they are only created once per process lifetime.
"""

import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings, PROJECT_ROOT

# Module-level caches: created on first access, reused thereafter
_embedding_model: HuggingFaceEmbeddings | None = None
_vector_store: Chroma | None = None

# Local model path — auto-discovered from the data/models directory if present
_LOCAL_MODEL_PATH = None
_local_candidate = os.path.join(PROJECT_ROOT, "data", "models", "models")
if os.path.isdir(_local_candidate):
    for entry in os.listdir(_local_candidate):
        snapshot = os.path.join(_local_candidate, entry, "snapshots", "master")
        if os.path.isdir(snapshot):
            _LOCAL_MODEL_PATH = snapshot
            break


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return the shared local embedding model instance, creating it on first call.
    Uses BAAI/bge-small-zh-v1.5 — a lightweight Chinese-optimized model that
    runs entirely offline once downloaded.
    """
    global _embedding_model
    if _embedding_model is None:
        model_name = _LOCAL_MODEL_PATH or "BAAI/bge-small-zh-v1.5"
        _embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model


def get_vector_store() -> Chroma:
    """
    Return the shared ChromaDB vector store instance, creating and connecting
    it on first call. The collection ``ecommerce_kb`` stores all knowledge
    base document embeddings and persists them to disk.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            collection_name="ecommerce_kb",
            embedding_function=get_embeddings(),
            persist_directory=settings.resolved_chroma_dir,
        )
    return _vector_store


def reset_vector_store():
    """
    Reset the vector store singleton. The next call to ``get_vector_store()``
    will reinitialize the ChromaDB connection. Useful after clearing the
    knowledge base completely.
    """
    global _vector_store
    _vector_store = None
