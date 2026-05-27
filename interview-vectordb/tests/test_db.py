import json
from unittest.mock import MagicMock

import pytest

from interview_vectordb.db import ProfileDB
from interview_vectordb.schema import InterviewExperience, InterviewProfile


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
def db(mock_openai):
    return ProfileDB()


def _make_experience(company="TestCo", position="Engineer", raw_text="Some interview text") -> InterviewExperience:
    return InterviewExperience(company=company, position=position, raw_text=raw_text)


def test_sanitize_key_basic():
    assert ProfileDB._sanitize_key("字节", "后端") == "字节_后端"


def test_sanitize_key_slashes():
    assert "/" not in ProfileDB._sanitize_key("a/b", "c\\d")
    assert "\\" not in ProfileDB._sanitize_key("a/b", "c\\d")


def test_sanitize_key_dotdot():
    key = ProfileDB._sanitize_key("..", "..")
    assert ".." not in key


def test_save_and_load_profile(db):
    profile = InterviewProfile(company="A", position="B", difficulty_tendency="senior", focus_areas=["x"])
    db.save_profile(profile)
    loaded = db.get_profile("A", "B")
    assert loaded is not None
    assert loaded.company == "A"
    assert loaded.position == "B"
    assert loaded.difficulty_tendency == "senior"
    assert loaded.focus_areas == ["x"]


def test_load_nonexistent_profile(db):
    assert db.get_profile("No", "Such") is None


def test_list_profiles_empty(db):
    assert db.list_profiles() == []


def test_list_profiles_with_data(db):
    db.save_profile(InterviewProfile(company="A", position="B"))
    db.save_profile(InterviewProfile(company="C", position="D"))
    profiles = db.list_profiles()
    assert len(profiles) == 2
    keys = {(p.company, p.position) for p in profiles}
    assert ("A", "B") in keys
    assert ("C", "D") in keys


def test_delete_profile(db):
    db.save_profile(InterviewProfile(company="A", position="B"))
    assert db.get_profile("A", "B") is not None
    db.delete_profile("A", "B")
    assert db.get_profile("A", "B") is None


def test_delete_nonexistent_profile(db):
    db.delete_profile("No", "Such")


def test_add_experiences(db):
    ids = db.add_experiences([_make_experience(), _make_experience()])
    assert len(ids) == 2
    assert all(isinstance(i, str) and len(i) > 0 for i in ids)


def test_get_experiences(db):
    db.add_experiences([_make_experience("A", "B"), _make_experience("A", "B")])
    exps = db.get_experiences("A", "B")
    assert len(exps) == 2
    assert all(e.company == "A" and e.position == "B" for e in exps)


def test_get_experiences_empty(db):
    assert db.get_experiences("No", "Such") == []


def test_generate_profile_single(db):
    db.add_experiences([_make_experience()])
    profile = db.generate_profile("TestCo", "Engineer")
    assert profile is not None
    assert profile.company == "TestCo"
    assert profile.position == "Engineer"
    assert profile.source_count == 1


def test_generate_profile_multiple(db):
    db.add_experiences([_make_experience(), _make_experience(), _make_experience()])
    profile = db.generate_profile("TestCo", "Engineer")
    assert profile is not None
    assert profile.company == "TestCo"
    assert profile.source_count == 3


def test_generate_profile_no_experiences(db):
    assert db.generate_profile("No", "Such") is None


def test_get_or_generate_profile_existing(db):
    db.save_profile(InterviewProfile(company="A", position="B", difficulty_tendency="senior"))
    profile = db.get_or_generate_profile("A", "B")
    assert profile.difficulty_tendency == "senior"


def test_get_or_generate_profile_new(db):
    db.add_experiences([_make_experience()])
    profile = db.get_or_generate_profile("TestCo", "Engineer")
    assert profile is not None
    assert profile.company == "TestCo"


def test_get_or_generate_no_experiences(db):
    profile = db.get_or_generate_profile("No", "Such")
    assert profile is not None
    assert profile.company == "No"
    assert profile.source_count == 0


def test_batch_generate_profiles(db):
    db.add_experiences([_make_experience("A", "B"), _make_experience("C", "D")])
    results = db.batch_generate_profiles()
    assert "A_B" in results
    assert "C_D" in results


def test_call_llm_failure(db, monkeypatch):
    def failing_create(self, **kwargs):
        raise RuntimeError("LLM down")

    monkeypatch.setattr("openai.resources.chat.completions.Completions.create", failing_create)
    result = db._call_llm("test prompt")
    assert result is None


def test_parse_profile_json_valid(db):
    content = json.dumps({
        "difficulty_tendency": "senior",
        "focus_areas": ["a"],
        "interview_style": "b",
        "question_types": ["c"],
        "key_traits": ["d"],
    })
    profile = db._parse_profile_json(content, "X", "Y", source_count=5)
    assert profile is not None
    assert profile.company == "X"
    assert profile.difficulty_tendency == "senior"
    assert profile.source_count == 5


def test_parse_profile_json_invalid(db):
    assert db._parse_profile_json("not json at all{{{", "X", "Y") is None


def test_parse_profile_json_with_markdown_fence(db, monkeypatch):
    def fake_create(self, **kwargs):
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "```json\n" + json.dumps({
            "difficulty_tendency": "mid",
            "focus_areas": [],
            "interview_style": "test",
            "question_types": [],
            "key_traits": [],
        }) + "\n```"
        return response

    monkeypatch.setattr("openai.resources.chat.completions.Completions.create", fake_create)
    stripped = db._call_llm("prompt")
    assert stripped is not None
    profile = db._parse_profile_json(stripped, "X", "Y")
    assert profile is not None
    assert profile.company == "X"
    assert profile.interview_style == "test"
