"""
Document loader: converts uploaded files into LangChain Document objects.

Supported formats: PDF, DOCX, DOC, TXT, MD, XLSX, XLS, CSV.
Each loader from langchain_community extracts text and metadata from the
respective file format and returns a list of Document objects.
"""

import os
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
    CSVLoader,
)


def load_document(file_path: str, ext: str) -> List:
    """
    Load a document file using the appropriate LangChain loader based on the
    file extension. Returns a list of langchain_core Document objects, each
    containing the extracted text and metadata.

    Raises ValueError if the file extension is not in the supported set.
    """
    # Mapping from lowercase file extension to loader class
    loaders = {
        ".pdf": PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".doc": Docx2txtLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".xls": UnstructuredExcelLoader,
        ".csv": CSVLoader,
    }

    loader_cls = loaders.get(ext)
    if not loader_cls:
        raise ValueError(f"Unsupported file type: {ext}")

    # Text-based files use UTF-8 encoding; binary formats (PDF, DOCX, etc.)
    # handle encoding internally through their respective libraries
    if ext in (".txt", ".md"):
        loader = loader_cls(file_path, encoding="utf-8")
    else:
        loader = loader_cls(file_path)

    docs = loader.load()
    # Ensure every document has a "source" metadata field for citation
    for doc in docs:
        if "source" not in doc.metadata:
            doc.metadata["source"] = os.path.basename(file_path)
    return docs
