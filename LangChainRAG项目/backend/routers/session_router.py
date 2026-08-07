"""
Session router: chat session CRUD and streaming Q&A endpoint.

Endpoints under ``/api/sessions``. All require authentication.
The /chat endpoint returns a Server-Sent Events (SSE) stream for real-time
token-by-token answer delivery.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, Session as DBSession, Message
from schemas import (
    SessionCreate, SessionInfo, MessageInfo, ChatRequest, DEFAULT_SESSION_TITLE,
)
from auth import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionInfo)
def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session for the current user."""
    session = DBSession(user_id=current_user.id, title=data.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionInfo.model_validate(session)


@router.get("", response_model=list[SessionInfo])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all chat sessions belonging to the current user, ordered by
    most recently updated first.
    """
    sessions = (
        db.query(DBSession)
        .filter(DBSession.user_id == current_user.id)
        .order_by(desc(DBSession.updated_at))
        .all()
    )
    return [SessionInfo.model_validate(s) for s in sessions]


@router.get("/{session_id}/messages", response_model=list[MessageInfo])
def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all messages in a session in chronological order.
    Access is scoped to the session owner — other users cannot read
    someone else's chat history.
    """
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(404, "会话不存在")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )
    return [MessageInfo.model_validate(m) for m in messages]


@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a chat session and all its messages (cascading delete).
    Only the session owner can delete it.
    """
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(404, "会话不存在")
    db.delete(session)
    db.commit()
    return {"message": "会话已删除"}


@router.put("/{session_id}", response_model=SessionInfo)
def update_session(
    session_id: int,
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename a chat session. Only the owner can rename it."""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(404, "会话不存在")
    session.title = data.title
    db.commit()
    db.refresh(session)
    return SessionInfo.model_validate(session)


@router.post("/chat")
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming Q&A chat endpoint using Server-Sent Events (SSE).

    The SSE stream emits three event types:
    - ``chunk``: a token of the generated answer (sent as it is generated)
    - ``sources``: the list of knowledge base sources that informed the answer
    - ``done``: signals the stream is complete

    After the stream finishes, the complete assistant message (with sources)
    is persisted to the database so it appears in the chat history.
    """
    # Verify the session exists and belongs to the current user
    session = db.query(DBSession).filter(DBSession.id == data.session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(404, "会话不存在")

    # Persist the user's question immediately
    user_msg = Message(
        session_id=data.session_id,
        role="user",
        content=data.question,
    )
    db.add(user_msg)

    # Auto-title: use first question to generate session title
    if session.title == DEFAULT_SESSION_TITLE:
        trimmed = data.question.strip()
        if trimmed:
            session.title = trimmed[:20] + ("..." if len(trimmed) > 20 else "")
        else:
            session.title = "未命名"

    db.commit()

    # Load the full message history (including the just-added user message)
    # for context-aware RAG retrieval
    history = (
        db.query(Message)
        .filter(Message.session_id == data.session_id)
        .order_by(Message.created_at)
        .all()
    )

    from rag.engine import rag_engine

    async def generate():
        """Async generator that yields SSE-formatted events."""
        full_answer = ""
        sources = []

        # Stream answer chunks from the RAG pipeline
        async for chunk, srcs in rag_engine.query_stream(data.question, history):
            if chunk:
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            if srcs:
                sources = srcs

        # Emit the source citations
        yield f"data: {json.dumps({'type': 'sources', 'content': sources}, ensure_ascii=False)}\n\n"

        # Persist assistant message and bump session timestamp before signalling done
        assistant_msg = Message(
            session_id=data.session_id,
            role="assistant",
            content=full_answer,
            sources=sources,
        )
        db.add(assistant_msg)
        session.updated_at = assistant_msg.created_at  # type: ignore
        db.commit()

        # Signal the end of the stream
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
