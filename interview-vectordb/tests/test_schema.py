import pytest
from pydantic import ValidationError

from interview_vectordb.schema import InterviewExperience, InterviewProfile


def test_interview_profile_defaults():
    p = InterviewProfile(company="A", position="B")
    assert p.company == "A"
    assert p.position == "B"
    assert p.difficulty_tendency == "mid"
    assert p.focus_areas == []
    assert p.interview_style == ""
    assert p.question_types == []
    assert p.key_traits == []
    assert p.source_count == 0


def test_interview_profile_with_data():
    p = InterviewProfile(
        company="字节",
        position="后端",
        difficulty_tendency="senior",
        focus_areas=["系统设计", "高并发"],
        interview_style="深挖底层",
        question_types=["原理题"],
        key_traits=["偏底层"],
        source_count=5,
    )
    assert p.company == "字节"
    assert p.position == "后端"
    assert p.difficulty_tendency == "senior"
    assert p.focus_areas == ["系统设计", "高并发"]
    assert p.interview_style == "深挖底层"
    assert p.question_types == ["原理题"]
    assert p.key_traits == ["偏底层"]
    assert p.source_count == 5


def test_interview_profile_from_dict():
    data = {
        "company": "腾讯",
        "position": "前端",
        "difficulty_tendency": "junior",
        "focus_areas": ["JS"],
        "interview_style": "基础扎实",
        "question_types": ["手写代码"],
        "key_traits": ["偏基础"],
        "source_count": 2,
    }
    p = InterviewProfile.model_validate(data)
    assert p.company == "腾讯"
    assert p.position == "前端"
    assert p.difficulty_tendency == "junior"
    assert p.focus_areas == ["JS"]
    assert p.source_count == 2


def test_interview_experience_defaults():
    e = InterviewExperience(company="A", position="B")
    assert e.company == "A"
    assert e.position == "B"
    assert e.raw_text == ""


def test_interview_experience_max_length():
    with pytest.raises(ValidationError):
        InterviewExperience(company="x" * 129, position="ok")
    with pytest.raises(ValidationError):
        InterviewExperience(company="ok", position="x" * 129)


def test_interview_experience_raw_text_max_length():
    with pytest.raises(ValidationError):
        InterviewExperience(company="A", position="B", raw_text="x" * 100001)
