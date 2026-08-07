"""Unit tests for auth.py – password hashing, JWT, get_current_user.

These tests exercise the pure authentication logic.
Database interactions are mocked where necessary.
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from models import User


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        h = hash_password("mypassword")
        assert h.startswith("$2b$")

    def test_same_password_different_hashes(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2  # bcrypt salts are random


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        h = hash_password("secret123")
        assert verify_password("secret123", h) is True

    def test_wrong_password_returns_false(self):
        h = hash_password("secret123")
        assert verify_password("wrong_password", h) is False

    def test_empty_string_password(self):
        h = hash_password("")
        assert verify_password("", h) is True


class TestCreateAccessToken:
    def test_returns_string_jwt(self):
        token = create_access_token({"sub": "42"})
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature

    def test_token_contains_sub_claim(self):
        from jose import jwt
        from config import settings as cfg
        token = create_access_token({"sub": "7"})
        payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
        assert payload["sub"] == "7"

    def test_token_has_expiration(self):
        from jose import jwt
        from config import settings as cfg
        token = create_access_token({"sub": "1"})
        payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
        assert "exp" in payload


class TestGetCurrentUser:
    def _make_credentials(self, token_str: str):
        from fastapi.security import HTTPAuthorizationCredentials
        return HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token_str,
        )

    def test_valid_token_returns_user(self):
        """get_current_user decodes token and fetches user from DB."""
        token = create_access_token({"sub": "1"})
        credentials = self._make_credentials(token)

        fake_user = User(id=1, username="test", is_admin=False)
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.first.return_value = fake_user

        result = get_current_user(credentials=credentials, db=fake_db)
        assert result.id == 1
        assert result.username == "test"

    def test_invalid_token_raises_401(self):
        credentials = self._make_credentials("not.a.real.token")
        fake_db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            get_current_user(credentials=credentials, db=fake_db)
        assert exc.value.status_code == 401

    def test_nonexistent_user_raises_401(self):
        token = create_access_token({"sub": "99999"})
        credentials = self._make_credentials(token)

        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            get_current_user(credentials=credentials, db=fake_db)
        assert exc.value.status_code == 401

    def test_token_without_sub_raises_type_error(self):
        """Token without 'sub' key → int(None) raises TypeError.

        This documents a latent bug: the code does not guard against
        a missing 'sub' claim before calling int() on it.
        """
        token = create_access_token({"role": "admin"})  # no "sub"
        credentials = self._make_credentials(token)

        fake_db = MagicMock()
        with pytest.raises(TypeError):
            get_current_user(credentials=credentials, db=fake_db)

    def test_token_with_none_sub(self):
        """Token where 'sub' is the *string* 'None' raises ValueError.

        int(\"None\") raises ValueError, which is NOT caught by the
        except JWTError block -- this is a latent bug in the production
        code.  The test documents the current behavior.
        """
        from jose import jwt as jose_jwt
        from config import settings as cfg
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": "None",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jose_jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)
        credentials = self._make_credentials(token)

        fake_db = MagicMock()
        with pytest.raises(ValueError):
            get_current_user(credentials=credentials, db=fake_db)
