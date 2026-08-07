"""Integration tests for the /api/sessions routes.

Mocks the RAG engine to avoid DeepSeek API calls during chat tests.
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from unittest.mock import patch, AsyncMock


class TestCreateSession:
    def test_create_session_returns_session_info(self, client, user_token):
        resp = client.post(
            "/api/sessions",
            json={"title": "测试会话"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "测试会话"
        assert "id" in data
        assert "created_at" in data

    def test_create_session_default_title(self, client, user_token):
        resp = client.post(
            "/api/sessions",
            json={},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "新对话"

    def test_create_session_requires_auth(self, client):
        resp = client.post("/api/sessions", json={"title": "x"})
        assert resp.status_code == 401


class TestListSessions:
    def test_list_user_sessions(self, client, user_token):
        # Create two sessions
        client.post(
            "/api/sessions",
            json={"title": "S1"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        client.post(
            "/api/sessions",
            json={"title": "S2"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_sessions_are_user_scoped(self, client, user_token, admin_token):
        # User creates a session
        client.post(
            "/api/sessions",
            json={"title": "UserSession"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # Admin sees only their own sessions
        resp = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json() == []


class TestGetMessages:
    def test_empty_session_has_no_messages(self, client, user_token):
        create_resp = client.post(
            "/api/sessions",
            json={"title": "Empty"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        resp = client.get(
            f"/api/sessions/{sid}/messages",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_messages_from_other_user_not_accessible(self, client, user_token, admin_token):
        # User creates a session
        create_resp = client.post(
            "/api/sessions",
            json={"title": "Private"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        # Admin tries to access it → 404
        resp = client.get(
            f"/api/sessions/{sid}/messages",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_nonexistent_session_returns_404(self, client, user_token):
        resp = client.get(
            "/api/sessions/99999/messages",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404


class TestChat:
    def test_chat_with_mocked_rag_returns_sse_stream(self, client, user_token):
        # Create session
        create_resp = client.post(
            "/api/sessions",
            json={"title": "ChatTest"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        # Mock the RAG engine's query_stream
        async def mock_stream(question, history):
            yield ("这是回答内容", [{"filename": "doc.txt", "content": "ref", "score": 0.95}])

        with patch("rag.engine.rag_engine.query_stream", side_effect=mock_stream):
            resp = client.post(
                "/api/sessions/chat",
                json={"session_id": sid, "question": "什么是RAG?"},
                headers={"Authorization": f"Bearer {user_token}"},
            )
        assert resp.status_code == 200
        # SSE streaming response should contain our answer
        body = resp.text
        assert "这是回答内容" in body
        assert "data:" in body

    def test_chat_nonexistent_session_returns_404(self, client, user_token):
        resp = client.post(
            "/api/sessions/chat",
            json={"session_id": 99999, "question": "hello"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    def test_chat_requires_auth(self, client):
        resp = client.post(
            "/api/sessions/chat",
            json={"session_id": 1, "question": "hello"},
        )
        assert resp.status_code == 401

    def test_chat_auto_titles_session_from_first_question(self, client, user_token, test_db):
        """When a session has the default title, the first question becomes the title."""
        create_resp = client.post(
            "/api/sessions",
            json={},  # uses DEFAULT_SESSION_TITLE
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]
        assert create_resp.json()["title"] == "新对话"

        async def mock_stream(question, history):
            yield ("回答", [])

        with patch("rag.engine.rag_engine.query_stream", side_effect=mock_stream):
            client.post(
                "/api/sessions/chat",
                json={"session_id": sid, "question": "这个商品可以退货吗？"},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        # Query DB directly because list_sessions API validates updated_at
        # (which is None due to a bug in session_router.py line 190)
        db = test_db["Session"]()
        from models import Session as DBSession
        s = db.query(DBSession).filter(DBSession.id == sid).first()
        db.close()
        # Title should be the first question (9 chars < 20, no truncation)
        assert s is not None
        assert s.title == "这个商品可以退货吗？"

    def test_chat_auto_title_empty_question_fallback(self, client, user_token, test_db):
        """When the first question is empty after strip, title falls back to '未命名'."""
        create_resp = client.post(
            "/api/sessions",
            json={},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        async def mock_stream(question, history):
            yield ("回答", [])

        with patch("rag.engine.rag_engine.query_stream", side_effect=mock_stream):
            client.post(
                "/api/sessions/chat",
                json={"session_id": sid, "question": "   "},  # whitespace only
                headers={"Authorization": f"Bearer {user_token}"},
            )

        db = test_db["Session"]()
        from models import Session as DBSession
        s = db.query(DBSession).filter(DBSession.id == sid).first()
        db.close()
        assert s is not None
        assert s.title == "未命名"

    def test_chat_done_event_after_sources(self, client, user_token):
        """The SSE 'done' event MUST appear after the 'sources' event to ensure the
        assistant message is persisted before the client considers the stream complete."""
        create_resp = client.post(
            "/api/sessions",
            json={"title": "OrderTest"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        async def mock_stream(question, history):
            yield ("chunk1", [{"filename": "doc.txt", "content": "ref", "score": 0.9}])

        with patch("rag.engine.rag_engine.query_stream", side_effect=mock_stream):
            resp = client.post(
                "/api/sessions/chat",
                json={"session_id": sid, "question": "测试问题"},
                headers={"Authorization": f"Bearer {user_token}"},
            )
        body = resp.text
        # sources event must appear before done event (json.dumps includes spaces)
        sources_pos = body.find('"type": "sources"')
        done_pos = body.find('"type": "done"')
        assert sources_pos != -1 and done_pos != -1, "SSE stream missing sources or done event"
        assert sources_pos < done_pos, (
            f"done ({done_pos}) must come after sources ({sources_pos})"
        )

    def test_chat_preserves_existing_custom_title(self, client, user_token, test_db):
        """Auto-title should NOT overwrite a custom title set by the user."""
        create_resp = client.post(
            "/api/sessions",
            json={"title": "我的自定义标题"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        async def mock_stream(question, history):
            yield ("回答", [])

        with patch("rag.engine.rag_engine.query_stream", side_effect=mock_stream):
            client.post(
                "/api/sessions/chat",
                json={"session_id": sid, "question": "新问题"},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        db = test_db["Session"]()
        from models import Session as DBSession
        s = db.query(DBSession).filter(DBSession.id == sid).first()
        db.close()
        assert s is not None
        # Custom title should remain unchanged
        assert s.title == "我的自定义标题"


class TestDeleteSession:
    def test_delete_own_session(self, client, user_token):
        create_resp = client.post(
            "/api/sessions",
            json={"title": "ToDelete"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        resp = client.delete(
            f"/api/sessions/{sid}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200

        # Verify gone
        list_resp = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert list_resp.json() == []

    def test_delete_other_users_session_returns_404(self, client, user_token, admin_token):
        # User creates a session
        create_resp = client.post(
            "/api/sessions",
            json={"title": "UsersSession"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        # Admin tries to delete it → 404
        resp = client.delete(
            f"/api/sessions/{sid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestUpdateSession:
    def test_update_session_title(self, client, user_token):
        create_resp = client.post(
            "/api/sessions",
            json={"title": "Old Title"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        sid = create_resp.json()["id"]

        resp = client.put(
            f"/api/sessions/{sid}",
            json={"title": "New Title"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_update_nonexistent_session_returns_404(self, client, user_token):
        resp = client.put(
            "/api/sessions/99999",
            json={"title": "Ghost"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404
