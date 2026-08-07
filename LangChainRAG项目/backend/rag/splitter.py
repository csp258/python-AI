"""
Text splitter: creates overlapping chunks from documents for embedding storage.

Uses LangChain's RecursiveCharacterTextSplitter with Chinese-punctuation-aware
separators. The separator list is ordered from most- to least-semantic boundary:
paragraph breaks split first, then sentences, then sub-sentence punctuation.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings


def get_splitter():
    """
    Return a configured text splitter that chunks documents into overlapping
    segments. Chunk size and overlap are read from application settings.

    Separators are ordered by semantic priority: double newlines (paragraphs)
    first, then single newlines, then Chinese/English sentence-ending punctuation,
    and finally individual whitespace characters as a last resort.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "！", "？", "；", "，", " ", ""],
        keep_separator=True,
    )
