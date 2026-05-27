import json

import pytest

from interview_tester.evaluator import _build_transcript, _parse_eval_json, build_evaluator_prompt
from interview_tester.schemas import QAPair, TestConfig, TestSession


def _make_session(**overrides) -> TestSession:
    cfg = TestConfig(**overrides)
    return TestSession(
        session_id="sid",
        config=cfg,
        started_at="2024-01-01T00:00:00+00:00",
        qa_pairs=[
            QAPair(
                round=1,
                question="问题1",
                answer="回答1",
                question_timestamp="2024-01-01T00:00:00+00:00",
                answer_timestamp="2024-01-01T00:00:05+00:00",
            ),
            QAPair(
                round=2,
                question="问题2",
                answer="回答2",
                question_timestamp="2024-01-01T00:01:00+00:00",
                answer_timestamp="2024-01-01T00:01:05+00:00",
            ),
        ],
    )


def test_build_evaluator_prompt_basic():
    prompt = build_evaluator_prompt(_make_session())
    for dim in [
        "style_naturalness：",
        "difficulty_appropriateness：",
        "follow_up_quality：",
        "topic_coverage：",
        "overall_score：",
        "difficulty_adaptation：",
    ]:
        assert dim in prompt
    assert "jd_relevance：" not in prompt
    assert "profile_relevance：" not in prompt


def test_build_evaluator_prompt_with_jd():
    prompt = build_evaluator_prompt(_make_session(job_description="后端，Python/Redis"))
    assert "jd_relevance：" in prompt
    assert "profile_relevance：" not in prompt


def test_build_evaluator_prompt_with_profile():
    prompt = build_evaluator_prompt(
        _make_session(profile_company="华为", profile_position="AI应用开发")
    )
    assert "profile_relevance：" in prompt
    assert "jd_relevance：" not in prompt


def test_build_evaluator_prompt_with_both():
    prompt = build_evaluator_prompt(
        _make_session(
            job_description="后端",
            profile_company="华为",
            profile_position="AI应用开发",
        )
    )
    for dim in [
        "style_naturalness",
        "difficulty_appropriateness",
        "follow_up_quality",
        "topic_coverage",
        "overall_score",
        "jd_relevance",
        "profile_relevance",
        "difficulty_adaptation",
    ]:
        assert dim in prompt


def test_build_evaluator_prompt_no_jd_note():
    prompt = build_evaluator_prompt(_make_session())
    assert "jd_relevance请评0分" in prompt


def test_build_evaluator_prompt_no_profile_note():
    prompt = build_evaluator_prompt(_make_session())
    assert "profile_relevance请评0分" in prompt


def test_build_transcript():
    session = _make_session()
    out = _build_transcript(session)
    assert "[第1轮] 面试官：问题1" in out
    assert "[第1轮] 候选人：回答1" in out
    assert "[第2轮] 面试官：问题2" in out
    assert "[第2轮] 候选人：回答2" in out


def test_parse_eval_json_plain():
    data = _parse_eval_json('{"a": 1, "b": "x"}')
    assert data == {"a": 1, "b": "x"}


def test_parse_eval_json_with_fence():
    text = '```json\n{"score": 7}\n```'
    assert _parse_eval_json(text) == {"score": 7}

    text2 = '```\n{"score": 8}\n```'
    assert _parse_eval_json(text2) == {"score": 8}


def test_parse_eval_json_invalid():
    with pytest.raises(json.JSONDecodeError):
        _parse_eval_json("not json at all")
