import json
from unittest.mock import MagicMock

from langchain_openai import ChatOpenAI

from interview_agent.config import LLMProviderConfig
from interview_agent.jd_parser import StructuredJD, parse_jd


def _provider() -> LLMProviderConfig:
    return LLMProviderConfig(base_url="http://localhost:1/v1", api_key="k", model="m")


def _patch_llm(monkeypatch, content):
    async def fake_ainvoke(self, messages, **kwargs):
        response = MagicMock()
        response.content = content
        return response

    monkeypatch.setattr(ChatOpenAI, "ainvoke", fake_ainvoke)


async def test_parse_jd_empty():
    result = await parse_jd("", _provider())
    assert result is None


async def test_parse_jd_whitespace():
    result = await parse_jd("   \n\t  ", _provider())
    assert result is None


async def test_parse_jd_truncation(monkeypatch):
    captured = {}

    async def fake_ainvoke(self, messages, **kwargs):
        captured["human"] = messages[-1].content
        response = MagicMock()
        response.content = json.dumps({"position_title": "X"})
        return response

    monkeypatch.setattr(ChatOpenAI, "ainvoke", fake_ainvoke)
    long_input = "A" * 5000
    await parse_jd(long_input, _provider())
    assert len(captured["human"]) == 4000


async def test_parse_jd_success(monkeypatch):
    payload = {
        "position_title": "Backend Engineer",
        "required_skills": ["Python", "PostgreSQL"],
        "required_experience": "3+ years",
        "key_responsibilities": ["Build APIs"],
        "preferred_qualifications": ["AWS"],
        "tech_stack": ["FastAPI"],
        "interview_focus": "system design",
    }
    _patch_llm(monkeypatch, json.dumps(payload))
    result = await parse_jd("some jd", _provider())
    assert isinstance(result, StructuredJD)
    assert result.position_title == "Backend Engineer"
    assert result.required_skills == ["Python", "PostgreSQL"]


async def test_parse_jd_with_markdown_fence(monkeypatch):
    payload = {"position_title": "Backend Engineer"}
    fenced = f"```json\n{json.dumps(payload)}\n```"
    _patch_llm(monkeypatch, fenced)
    result = await parse_jd("some jd", _provider())
    assert result is None or result.position_title == "Backend Engineer"


async def test_parse_jd_llm_failure(monkeypatch):
    async def fail(self, messages, **kwargs):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(ChatOpenAI, "ainvoke", fail)
    result = await parse_jd("some jd", _provider())
    assert result is None


async def test_parse_jd_invalid_json(monkeypatch):
    _patch_llm(monkeypatch, "this is not json at all")
    result = await parse_jd("some jd", _provider())
    assert result is None


def test_structured_jd_model():
    s = StructuredJD(
        position_title="X",
        required_skills=["a", "b"],
        required_experience="1y",
        key_responsibilities=["r"],
        preferred_qualifications=["q"],
        tech_stack=["t"],
        interview_focus="focus",
    )
    assert s.position_title == "X"
    assert s.required_skills == ["a", "b"]
    assert s.interview_focus == "focus"


def test_structured_jd_defaults():
    s = StructuredJD()
    assert s.position_title == ""
    assert s.required_skills == []
    assert s.required_experience == ""
    assert s.key_responsibilities == []
    assert s.preferred_qualifications == []
    assert s.tech_stack == []
    assert s.interview_focus == ""
