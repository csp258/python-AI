"""Integration tests for the /api/auth routes.

Uses the FastAPI TestClient with a real (temp-file) SQLite database.
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


class TestRegister:
    def test_register_creates_user_and_returns_token(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["is_admin"] is False

    def test_register_duplicate_username_returns_400(self, client):
        client.post("/api/auth/register", json={
            "username": "dupeuser",
            "password": "password123",
        })
        resp = client.post("/api/auth/register", json={
            "username": "dupeuser",
            "password": "another456",
        })
        assert resp.status_code == 400

    def test_register_short_password_fails_validation(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "shortpw",
            "password": "ab",  # min_length=6
        })
        assert resp.status_code == 422

    def test_register_short_username_fails_validation(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "x",  # min_length=2
            "password": "validpass123",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_with_correct_credentials(self, client):
        # Register first
        client.post("/api/auth/register", json={
            "username": "loginuser",
            "password": "mypassword",
        })
        resp = client.post("/api/auth/login", json={
            "username": "loginuser",
            "password": "mypassword",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "loginuser"

    def test_login_with_wrong_password_returns_401(self, client):
        client.post("/api/auth/register", json={
            "username": "wrongpw",
            "password": "correctpass",
        })
        resp = client.post("/api/auth/login", json={
            "username": "wrongpw",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "ghostuser",
            "password": "anything",
        })
        assert resp.status_code == 401


class TestGetMe:
    def test_with_valid_token_returns_user_info(self, client, user_token):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "username" in data
        assert "is_admin" in data
        assert "created_at" in data

    def test_without_token_returns_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_with_invalid_token_returns_401(self, client):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert resp.status_code == 401


class TestChangePassword:
    def test_change_password_succeeds(self, client, user_token):
        resp = client.put(
            "/api/auth/change-password",
            json={"old_password": "password123", "new_password": "newpass456"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "密码修改成功"

    def test_change_password_wrong_old_password(self, client, user_token):
        resp = client.put(
            "/api/auth/change-password",
            json={"old_password": "wrongold", "new_password": "newpass456"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 400

    def test_change_password_requires_auth(self, client):
        resp = client.put(
            "/api/auth/change-password",
            json={"old_password": "old", "new_password": "newpass456"},
        )
        assert resp.status_code == 401
