"""Tests for config.py – Settings & path resolution."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config import Settings, settings, PROJECT_ROOT, _resolve_path


class TestProjectRoot:
    def test_project_root_exists(self):
        assert os.path.isdir(PROJECT_ROOT)

    def test_project_root_is_parent_of_backend(self):
        assert os.path.basename(PROJECT_ROOT).startswith("LangChain")

    def test_project_root_contains_env_file(self):
        env_path = os.path.join(PROJECT_ROOT, ".env")
        assert os.path.isfile(env_path)


class TestResolvePath:
    def test_relative_path_resolves_to_absolute(self):
        result = _resolve_path("./data/app.db")
        assert os.path.isabs(result)
        assert result.startswith(PROJECT_ROOT)

    def test_absolute_path_passes_through(self):
        result = _resolve_path("/absolute/path")
        assert result == "/absolute/path"

    def test_non_dot_prefix_passes_through(self):
        result = _resolve_path("data/app.db")
        assert result == "data/app.db"


class TestSettings:
    def test_defaults_exist(self):
        assert settings.deepseek_base_url == "https://api.deepseek.com"
        assert settings.jwt_algorithm == "HS256"
        assert settings.admin_username == "admin"
        assert settings.chunk_size == 800
        assert settings.top_k == 5

    def test_deepseek_api_key_is_set(self):
        assert settings.deepseek_api_key
        assert len(settings.deepseek_api_key) > 0

    def test_resolved_database_url_is_absolute(self):
        url = settings.resolved_database_url
        assert url.startswith("sqlite:///")
        bare = url.replace("sqlite:///", "")
        assert os.path.isabs(bare)

    def test_resolved_chroma_dir_is_absolute(self):
        d = settings.resolved_chroma_dir
        assert os.path.isabs(d)

    def test_resolved_upload_dir_is_absolute(self):
        d = settings.resolved_upload_dir
        assert os.path.isabs(d)

    def test_jwt_expire_minutes_positive(self):
        assert settings.jwt_expire_minutes > 0

    def test_max_upload_size_positive(self):
        assert settings.max_upload_size > 0
