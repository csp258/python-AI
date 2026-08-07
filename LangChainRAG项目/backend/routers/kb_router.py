"""
Knowledge base router: document CRUD and chunk inspection.

Endpoints under ``/api/knowledge``.
- Listing documents requires authentication.
- Upload, delete, and chunk inspection require admin privileges.
"""

import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, Document
from schemas import DocumentInfo, DocumentDelete
from auth import require_admin, get_current_user
from config import settings

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


@router.get("/documents", response_model=list[DocumentInfo])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all knowledge base documents ordered by creation time (newest first).
    Any authenticated user can view the document list.
    """
    docs = (
        db.query(Document)
        .order_by(desc(Document.created_at))
        .all()
    )
    return [DocumentInfo.model_validate(d) for d in docs]


@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Upload a knowledge base document (admin only).

    The file is validated for extension and size, then saved to disk under
    a UUID-based filename to prevent path traversal and name collisions.
    After saving, the file is indexed into the vector store; if indexing
    fails, the database record and disk file are rolled back.
    """
    # Validate file extension against the allowlist
    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed = {".pdf", ".txt", ".md", ".docx", ".doc", ".xlsx", ".xls", ".csv"}
    if ext not in allowed:
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    # Read and validate file size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(400, "文件过大，上限50MB")

    # Save with a UUID filename to avoid path traversal and overwriting
    upload_dir = settings.resolved_upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create database record
    doc = Document(
        filename=file.filename,
        file_type=ext.lstrip("."),
        file_path=file_path,
        file_size=len(content),
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Index into vector store; if it fails, roll back DB and disk
    try:
        from rag.engine import index_document
        chunk_count = index_document(doc.id, file_path, ext)
        doc.chunk_count = chunk_count
        db.commit()
        db.refresh(doc)
    except Exception as e:
        logger.error("Document indexing failed for doc_id=%d: %s", doc.id, e)
        db.delete(doc)
        db.commit()
        os.remove(file_path)
        raise HTTPException(500, "文档处理失败，请检查文件格式是否为支持的PDF/TXT/MD/DOCX/XLSX/CSV格式")

    return DocumentInfo.model_validate(doc)


@router.delete("/documents")
def delete_documents(
    data: DocumentDelete,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Batch-delete knowledge base documents (admin only).
    For each document ID in the request, the vector store chunks are removed
    and the file on disk is deleted.
    """
    from rag.engine import remove_document
    for doc_id in data.document_ids:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            remove_document(doc_id, doc.filename)
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            db.delete(doc)
    db.commit()
    return {"message": f"已删除 {len(data.document_ids)} 个文档"}


@router.get("/documents/{doc_id}/chunks")
def get_chunks(
    doc_id: int,
    current_user: User = Depends(require_admin),
):
    """
    Retrieve chunk previews for a specific document (admin only).
    Returns the first 300 characters of each chunk for inspection.
    """
    from rag.engine import get_document_chunks
    return get_document_chunks(doc_id)
