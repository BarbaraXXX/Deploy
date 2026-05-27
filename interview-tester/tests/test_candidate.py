import pytest
from langchain_openai import ChatOpenAI

from interview_tester.candidate import (
    _STYLE_PROMPTS,
    _VALID_STYLES,
    build_candidate_llm,
    get_candidate_system_prompt,
)


def test_valid_styles():
    assert _VALID_STYLES == {
        "cooperative",
        "weak",
        "evasive",
        "overconfident",
        "specific_weakness",
    }


def test_get_candidate_system_prompt_cooperative():
    prompt = get_candidate_system_prompt("backend", "mid", "cooperative")
    for style_text in _STYLE_PROMPTS.values():
        assert style_text not in prompt


def test_get_candidate_system_prompt_weak():
    prompt = get_candidate_system_prompt("backend", "mid", "weak")
    assert _STYLE_PROMPTS["weak"] in prompt


def test_get_candidate_system_prompt_evasive():
    prompt = get_candidate_system_prompt("backend", "mid", "evasive")
    assert _STYLE_PROMPTS["evasive"] in prompt


def test_get_candidate_system_prompt_overconfident():
    prompt = get_candidate_system_prompt("backend", "mid", "overconfident")
    assert _STYLE_PROMPTS["overconfident"] in prompt


def test_get_candidate_system_prompt_specific_weakness_with_list():
    prompt = get_candidate_system_prompt(
        "backend", "mid", "specific_weakness", ["分布式系统", "消息队列"]
    )
    assert "分布式系统" in prompt
    assert "消息队列" in prompt


def test_get_candidate_system_prompt_specific_weakness_without_list():
    prompt = get_candidate_system_prompt("backend", "mid", "specific_weakness", [])
    for style_text in _STYLE_PROMPTS.values():
        assert style_text not in prompt
    assert "不擅长的领域" not in prompt


def test_get_candidate_system_prompt_unknown_style():
    prompt = get_candidate_system_prompt("backend", "mid", "totally_made_up")
    for style_text in _STYLE_PROMPTS.values():
        assert style_text not in prompt
    assert "不擅长的领域" not in prompt


def test_get_candidate_system_prompt_junior():
    prompt = get_candidate_system_prompt("backend", "junior", "cooperative")
    assert "1-3年" in prompt
    assert "展示基础知识的掌握" in prompt


def test_get_candidate_system_prompt_senior():
    prompt = get_candidate_system_prompt("backend", "senior", "cooperative")
    assert "5年以上" in prompt
    assert "丰富的架构设计经验" in prompt


def test_get_candidate_system_prompt_domain_included():
    prompt = get_candidate_system_prompt("游戏服务端", "mid", "cooperative")
    assert "游戏服务端" in prompt


def test_build_candidate_llm(monkeypatch):
    from interview_agent.config import LLMProviderConfig, llm_settings

    provider = LLMProviderConfig(
        base_url="http://localhost:1/v1",
        api_key="test-key",
        model="test-model",
    )
    original = llm_settings.get_provider
    monkeypatch.setattr(type(llm_settings), "get_provider", lambda self, name=None: provider)
    try:
        llm = build_candidate_llm("mid")
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "test-model"
        assert llm.temperature == pytest.approx(0.7)
        assert "http://localhost:1/v1" in str(llm.openai_api_base)
    finally:
        monkeypatch.setattr(type(llm_settings), "get_provider", original)
