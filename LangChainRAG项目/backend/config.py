"""
Application configuration loaded from environment variables and a .env file.

Uses Pydantic Settings to read from the .env file at the project root.
All ``./data/`` relative paths are resolved to absolute paths at runtime
so the application works correctly regardless of the working directory.
"""

import os
from pydantic_settings import BaseSettings

# Project root: the directory that CONTAINS the backend/ directory (i.e., parent of this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_path(p: str) -> str:
    """
    Convert a relative path starting with ``./data/`` to an absolute path
    under the project root directory. Paths that are already absolute or use
    a different prefix are returned unchanged.
    """
    if p.startswith("./"):
        return os.path.join(PROJECT_ROOT, p[2:])
    return p


class Settings(BaseSettings):
    """
    Central configuration class. Every setting can be overridden by an
    environment variable or a ``.env`` file entry.

    Sensitive values (API keys, JWT secret) MUST come from the .env file
    and are NOT committed to version control.
    """

    # -- DeepSeek LLM / Embedding API --
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # -- JWT Authentication --
    jwt_secret_key: str = "change-in-production"  # SECURITY: override in .env for prod
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # token lifetime: 24 hours by default

    # -- SQLite Database --
    database_url: str = "sqlite:///./data/app.db"

    # -- ChromaDB Vector Store --
    chroma_persist_dir: str = "./data/chroma_db"

    # -- Default Admin Account (seeded on first startup) --
    admin_username: str = "admin"
    admin_password: str = "123456"  # SECURITY: change via .env for any non-local deployment

    # -- File Upload --
    upload_dir: str = "./data/uploads"
    max_upload_size: int = 52428800  # 50 MB upload limit

    # -- Document Chunking --
    chunk_size: int = 800  # target characters per text chunk
    chunk_overlap: int = 150  # character overlap between adjacent chunks
    top_k: int = 5  # default number of retrieval results

    # Tell Pydantic to load settings from the .env file at the project root
    model_config = {
        "env_file": os.path.join(PROJECT_ROOT, ".env"),
        "env_file_encoding": "utf-8",
    }

    @property
    def resolved_database_url(self) -> str:
        """
        Convert the SQLite relative-path URL to an absolute path so that
        the database file is always found relative to the project root,
        regardless of the current working directory.
        """
        if "sqlite:///./" in self.database_url:
            rel = self.database_url.replace("sqlite:///./", "")
            abs_path = os.path.join(PROJECT_ROOT, rel)
            return f"sqlite:///{abs_path}"
        return self.database_url

    @property
    def resolved_chroma_dir(self) -> str:
        """Absolute path to the ChromaDB persistence directory."""
        return _resolve_path(self.chroma_persist_dir)

    @property
    def resolved_upload_dir(self) -> str:
        """Absolute path to the file upload directory."""
        return _resolve_path(self.upload_dir)


# Module-level singleton: imported by all other modules that need configuration
settings = Settings()
