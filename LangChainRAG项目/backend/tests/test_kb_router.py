"""Integration tests for the /api/knowledge routes.

Mocks the RAG engine (ChromaDB + embeddings) to avoid external calls.
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import io
from unittest.mock import patch
from config import settings as cfg_settings


class TestListDocuments:
    def test_empty_list_initially(self, client, admin_token):
        resp = client.get(
            "/api/knowledge/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_requires_authentication(self, client):
        resp = client.get("/api/knowledge/documents")
        assert resp.status_code == 401


class TestUploadDocument:
    def test_upload_txt_as_admin(self, client, admin_token):
        with patch("rag.engine.index_document", return_value=3):
            resp = client.post(
                "/api/knowledge/upload",
                files={"file": ("test.txt", io.BytesIO(b"Hello world content"), "text/plain")},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "test.txt"
        assert data["file_type"] == "txt"
        assert data["chunk_count"] == 3

    def test_upload_as_non_admin_fails(self, client, user_token):
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_upload_without_auth_fails(self, client):
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
        )
        assert resp.status_code == 401

    def test_upload_invalid_extension(self, client, admin_token):
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("image.png", io.BytesIO(b"fake"), "image/png")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    def test_upload_exceeding_size_limit(self, client, admin_token, monkeypatch):
        # Lower the size limit on the settings singleton for this test
        monkeypatch.setattr(cfg_settings, "max_upload_size", 10)
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("big.txt", io.BytesIO(b"x" * 100), "text/plain")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    def test_upload_then_list_documents(self, client, admin_token):
        with patch("rag.engine.index_document", return_value=2):
            resp = client.post(
                "/api/knowledge/upload",
                files={"file": ("doc1.txt", io.BytesIO(b"First doc"), "text/plain")},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200

        resp = client.get(
            "/api/knowledge/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 1
        assert docs[0]["filename"] == "doc1.txt"


class TestDeleteDocuments:
    def test_delete_as_admin(self, client, admin_token):
        # Upload first
        with patch("rag.engine.index_document", return_value=1):
            upload_resp = client.post(
                "/api/knowledge/upload",
                files={"file": ("todel.txt", io.BytesIO(b"delete me"), "text/plain")},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert upload_resp.status_code == 200
            doc_id = upload_resp.json()["id"]

        # Delete it
        with patch("rag.engine.remove_document"):
            resp = client.request(
                "DELETE", "/api/knowledge/documents",
                json={"document_ids": [doc_id]},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert resp.status_code == 200

        # Verify it's gone
        list_resp = client.get(
            "/api/knowledge/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert len(list_resp.json()) == 0

    def test_delete_as_non_admin_fails(self, client, user_token):
        resp = client.request(
            "DELETE", "/api/knowledge/documents",
            json={"document_ids": [1]},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_delete_without_auth_fails(self, client):
        resp = client.request(
            "DELETE", "/api/knowledge/documents",
            json={"document_ids": [1]},
        )
        assert resp.status_code == 401
