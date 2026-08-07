"""
Pydantic v2 schemas for request/response validation and serialization.

Each schema maps to an API operation: request bodies are validated on input,
and response models are serialized from ORM objects (via ``from_attributes=True``).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Annotated
from datetime import datetime, timezone
from pydantic.functional_serializers import PlainSerializer

# Serialize naive datetimes as UTC so JavaScript correctly parses them.
# SQLite strips timezone info, so all stored datetimes are naive UTC.
UtcDateTime = Annotated[
    datetime,
    PlainSerializer(
        lambda dt: (dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt).isoformat(),
        return_type=str,
    ),
]


class UserRegister(BaseModel):
    """Request body for the register endpoint. Enforces username/password length limits."""
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Request body for the login endpoint."""
    username: str
    password: str


class UserInfo(BaseModel):
    """
    Public user profile returned in API responses. Note: the password hash is NEVER
    included in this schema to prevent accidental exposure.
    """
    id: int
    username: str
    is_admin: bool
    created_at: UtcDateTime

    model_config = {"from_attributes": True}


class ChangePassword(BaseModel):
    """Request body for changing the current user's password."""
    old_password: str
    new_password: str = Field(min_length=6, max_length=100)


class Token(BaseModel):
    """Response for login/register: contains the JWT access token and user profile."""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


DEFAULT_SESSION_TITLE = "新对话"


class SessionCreate(BaseModel):
    """Request body for creating a new chat session."""
    title: str = DEFAULT_SESSION_TITLE


class SessionInfo(BaseModel):
    """Response model for a chat session."""
    id: int
    title: str
    created_at: UtcDateTime
    updated_at: UtcDateTime

    model_config = {"from_attributes": True}


class MessageInfo(BaseModel):
    """
    Response model for a chat message. ``sources`` is a JSON list of
    {filename, content, score} dicts representing the knowledge base chunks
    that informed the assistant's answer.
    """
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: UtcDateTime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """Request body for the streaming chat endpoint."""
    session_id: int
    question: str


class ChatResponse(BaseModel):
    """Non-streaming chat response (used for FAQ cache hits and error messages)."""
    answer: str
    sources: List[dict] = []


class DocumentInfo(BaseModel):
    """Response model for a knowledge base document."""
    id: int
    filename: str
    file_type: str
    chunk_count: int
    file_size: int
    created_at: UtcDateTime

    model_config = {"from_attributes": True}


class DocumentDelete(BaseModel):
    """Request body for batch-deleting knowledge base documents by ID."""
    document_ids: List[int]
