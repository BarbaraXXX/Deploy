import json
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from interview_vectordb import api as api_module
from interview_vectordb.api import api_app
from interview_vectordb.db import ProfileDB
from interview_vectordb.schema import InterviewProfile


@pytest.fixture
def mock_openai(monkeypatch):
    def fake_create(self, **kwargs):
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = json.dumps({
            "difficulty_tendency": "mid",
            "focus_areas": ["system design"],
            "interview_style": "deep dive",
            "question_types": ["principle"],
            "key_traits": ["bottom-up"],
        })
        return response

    monkeypatch.setattr("openai.OpenAI.__init__", lambda self, **kw: None)
    monkeypatch.setattr("openai.resources.chat.completions.Completions.create", fake_create)


@pytest.fixture
def test_db(mock_openai, isolate_env, monkeypatch):
    fresh_db = ProfileDB()
    monkeypatch.setattr(api_module, "_db", fresh_db)
    monkeypatch.setattr(api_module, "_EXPERIENCES_DIR", isolate_env / "experiences")
    return fresh_db


@pytest.fixture
async def client(test_db):
    async with AsyncClient(transport=ASGITransport(app=api_app), base_url="http://test") as c:
        yield c


async def test_list_profiles_empty(client):
    r = await client.get("/api/profiles")
    assert r.status_code == 200
    assert r.json() == {"profiles": []}


async def test_list_profiles_with_data(client, test_db):
    test_db.save_profile(InterviewProfile(company="A", position="B", source_count=3))
    r = await client.get("/api/profiles")
    assert r.status_code == 200
    body = r.json()
    assert len(body["profiles"]) == 1
    assert body["profiles"][0]["company"] == "A"
    assert body["profiles"][0]["position"] == "B"
    assert body["profiles"][0]["source_count"] == 3


async def test_get_profile(client, test_db):
    test_db.save_profile(InterviewProfile(company="A", position="B", difficulty_tendency="senior"))
    r = await client.get("/api/profiles/A/B")
    assert r.status_code == 200
    body = r.json()
    assert body["company"] == "A"
    assert body["difficulty_tendency"] == "senior"


async def test_get_profile_not_found_triggers_generate(client, test_db):
    from interview_vectordb.schema import InterviewExperience
    test_db.add_experiences([InterviewExperience(company="X", position="Y", raw_text="some text")])
    r = await client.get("/api/profiles/X/Y")
    assert r.status_code == 200
    body = r.json()
    assert body["company"] == "X"
    assert body["position"] == "Y"


async def test_delete_profile(client, test_db):
    test_db.save_profile(InterviewProfile(company="A", position="B"))
    r = await client.delete("/api/profiles/A/B")
    assert r.status_code == 200
    assert r.json() == {"deleted": "A_B"}
    assert test_db.get_profile("A", "B") is None


async def test_generate_profile(client, test_db):
    from interview_vectordb.schema import InterviewExperience
    test_db.add_experiences([InterviewExperience(company="A", position="B", raw_text="text")])
    r = await client.post("/api/profiles/A/B/generate")
    assert r.status_code == 200
    body = r.json()
    assert body["company"] == "A"
    assert body["source_count"] == 1


async def test_generate_profile_no_experiences(client):
    r = await client.post("/api/profiles/No/Such/generate")
    assert r.status_code == 200
    assert r.json() == {"error": "No experiences found for this company/position"}


async def test_experiences_count(client, test_db):
    from interview_vectordb.schema import InterviewExperience
    test_db.add_experiences([
        InterviewExperience(company="A", position="B", raw_text="x"),
        InterviewExperience(company="A", position="B", raw_text="y"),
        InterviewExperience(company="C", position="D", raw_text="z"),
    ])
    r = await client.get("/api/experiences/count")
    assert r.status_code == 200
    body = r.json()
    assert body["counts"]["A_B"] == 2
    assert body["counts"]["C_D"] == 1


async def test_import_experiences(client, test_db):
    payload = [
        {"company": "A", "position": "B", "raw_text": "x"},
        {"company": "C", "position": "D", "raw_text": "y"},
    ]
    r = await client.post("/api/experiences/import", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 2
    assert len(body["ids"]) == 2


async def test_import_experiences_too_many(client):
    payload = [{"company": "A", "position": "B", "raw_text": "x"} for _ in range(501)]
    r = await client.post("/api/experiences/import", json=payload)
    assert r.status_code == 400


async def test_validate_path_segment_empty(client):
    r = await client.get("/api/profiles/%20/B")
    assert r.status_code == 400


async def test_validate_path_segment_traversal(client):
    r = await client.get("/api/profiles/..etc/B")
    assert r.status_code == 400
