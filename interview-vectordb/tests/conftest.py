import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:1/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("MCP_SERVER_PORT", "9000")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    profiles_dir = data_dir / "profiles"
    profiles_dir.mkdir()
    experiences_dir = data_dir / "experiences"
    experiences_dir.mkdir()

    monkeypatch.setattr("interview_vectordb.db._DATA_DIR", data_dir)
    monkeypatch.setattr("interview_vectordb.db._PROFILES_DIR", profiles_dir)
    monkeypatch.setattr("interview_vectordb.db._EXPERIENCES_DIR", experiences_dir)

    yield data_dir
