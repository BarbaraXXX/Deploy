import json

import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "test")
    monkeypatch.setenv("LLM_PROVIDERS", json.dumps({
        "test": {"base_url": "http://localhost:1/v1", "api_key": "test-key", "model": "test-model"}
    }))
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("MCP_SERVER_URLS", "")
    monkeypatch.setenv("VECTORDB_BASE_URL", "http://localhost:1")

    data_dir = tmp_path / "data" / "sessions"
    data_dir.mkdir(parents=True)
    monkeypatch.setattr("interview_tester.config.test_settings.data_dir", data_dir)

    yield data_dir
