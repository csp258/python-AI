"""
FastAPI application entry point.

Starts the e-commerce RAG knowledge base Q&A system with:
- Automatic database table creation on startup
- Admin account seeding (creates the admin user if it does not exist)
- CORS configuration for local frontend dev servers (Vite on port 5173, etc.)
- Router registration for auth, knowledge base, and session management
"""

import sys
import os

# Ensure the backend package is importable when running as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, SessionLocal
from auth import hash_password
from models import User
from config import settings
from routers import auth_router, kb_router, session_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager: runs startup logic before the server
    begins accepting requests and cleanup logic after shutdown.

    On startup: creates database tables and seeds the default admin account.
    """
    init_db()
    _seed_admin()
    yield


def _seed_admin():
    """
    Create the default admin account if it does not already exist in the database.

    Uses credentials from application settings (overridable via .env).
    This is safe to call on every startup because it checks for an existing admin first.
    """
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.admin_username).first()
        if not existing:
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


app = FastAPI(title="电商RAG知识库问答系统", version="1.0.0", lifespan=lifespan)

# CORS: allow the local frontend dev server(s) to call the API.
# In production, these origins should be tightened to the actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API route modules
app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(session_router)


@app.get("/api/health")
def health():
    """Simple liveness probe: returns 200 OK when the server is running."""
    return {"status": "ok"}
