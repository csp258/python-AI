"""
Database module: SQLAlchemy engine, session factory, and ORM base.

Uses SQLite via the resolved database URL from application settings.
The ``check_same_thread=False`` flag is required because FastAPI serves requests
from multiple threads, and SQLite normally disallows cross-thread connections.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# Create the SQLAlchemy engine with thread-safe SQLite configuration
engine = create_engine(
    settings.resolved_database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

# SessionLocal is a factory for per-request database sessions; each HTTP request
# gets its own session via the get_db dependency
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base: all ORM model classes inherit from this to map to database tables
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is closed
    after the request completes, even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all database tables defined by ORM models. Safe to call on every
    startup because CREATE TABLE IF NOT EXISTS semantics are used internally.
    """
    Base.metadata.create_all(bind=engine)
