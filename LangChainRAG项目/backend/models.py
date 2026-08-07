"""
SQLAlchemy ORM models for the e-commerce RAG knowledge base system.

Tables:
- users: registered accounts (admin or regular user)
- sessions: chat conversation sessions, owned by a user
- messages: individual user/assistant messages within a session
- documents: files uploaded to the knowledge base by an admin
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def utcnow():
    """Return the current UTC datetime, used as a column default for timestamps."""
    return datetime.now(timezone.utc)


class User(Base):
    """
    Registered user account.

    Admins can upload and manage knowledge base documents; regular users can
    only participate in chat sessions.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)  # bcrypt hash, never store plaintext
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    # Cascading deletes: removing a user also removes their sessions and uploaded documents
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploader", cascade="all, delete-orphan")


class Session(Base):
    """
    A chat conversation session belonging to one user.

    Each session contains an ordered list of messages. The ``updated_at`` timestamp
    is automatically bumped whenever a new message is added.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)  # auto-updated by SQLAlchemy

    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message", back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",  # messages are always ordered chronologically
    )


class Message(Base):
    """
    A single Q&A message in a session.

    ``role`` is either "user" or "assistant".
    ``sources`` stores JSON data about the knowledge base chunks that informed the answer,
    used for displaying references in the frontend.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # list of {filename, content, score} dicts
    created_at = Column(DateTime, default=utcnow)

    session = relationship("Session", back_populates="messages")


class Document(Base):
    """
    A knowledge base document uploaded by an admin.

    The file is stored on disk under ``upload_dir``; this table records metadata
    and a reference path. ``chunk_count`` tracks how many text chunks were created
    from this document during indexing.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(300), nullable=False)  # original filename submitted by the user
    file_type = Column(String(20), nullable=False)  # file extension without the dot
    file_path = Column(String(500), nullable=False)  # absolute path to the stored file
    chunk_count = Column(Integer, default=0)  # number of vector-store chunks created
    file_size = Column(Integer, default=0)  # size in bytes
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    uploader = relationship("User", back_populates="documents")
