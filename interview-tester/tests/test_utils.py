
from interview_tester.utils import (
    fetch_profile,
    format_jd,
    format_profile,
    is_interview_ending,
    sanitize_path_segment,
)


def test_is_interview_ending_true():
    assert is_interview_ending("好的，面试结束了，谢谢") is True


def test_is_interview_ending_true_greeting():
    assert is_interview_ending("感谢参与本次活动") is True


def test_is_interview_ending_false():
    assert is_interview_ending("请介绍一下你的项目经验") is False


def test_is_interview_ending_case_insensitive():
    assert is_interview_ending("Overall evaluation incoming") is True


def test_is_interview_ending_partial():
    # Documented current behavior: "总结" alone is considered an ending signal.
    assert is_interview_ending("总结") is True


def test_sanitize_path_segment_normal():
    assert sanitize_path_segment("hello world") == "hello world"


def test_sanitize_path_segment_traversal():
    assert sanitize_path_segment("..") == ""
    assert sanitize_path_segment("foo/../bar") == ""


def test_sanitize_path_segment_slash():
    assert sanitize_path_segment("foo/bar") == ""


def test_sanitize_path_segment_backslash():
    assert sanitize_path_segment("foo\\bar") == ""


def test_sanitize_path_segment_length():
    raw = "a" * 200
    out = sanitize_path_segment(raw)
    assert len(out) == 128
    assert out == "a" * 128


def test_format_jd_full():
    from interview_agent.jd_parser import StructuredJD

    jd = StructuredJD(
        position_title="后端工程师",
        required_skills=["Python", "Redis"],
        required_experience="3-5年",
        key_responsibilities=["设计", "开发"],
        preferred_qualifications=["有云原生经验"],
        tech_stack=["FastAPI", "PostgreSQL"],
        interview_focus="架构设计",
    )
    out = format_jd(jd)
    assert "岗位：后端工程师" in out
    assert "经验要求：3-5年" in out
    assert "必需技能：Python, Redis" in out
    assert "技术栈：FastAPI, PostgreSQL" in out
    assert "核心职责：" in out
    assert "- 设计" in out
    assert "- 开发" in out
    assert "加分项：" in out
    assert "- 有云原生经验" in out
    assert "面试侧重：架构设计" in out


def test_format_jd_empty():
    from interview_agent.jd_parser import StructuredJD

    jd = StructuredJD()
    assert format_jd(jd) == ""


def test_format_jd_partial():
    from interview_agent.jd_parser import StructuredJD

    jd = StructuredJD(position_title="前端", required_skills=["React"])
    out = format_jd(jd)
    assert "岗位：前端" in out
    assert "必需技能：React" in out
    assert "经验要求" not in out
    assert "技术栈" not in out
    assert "核心职责" not in out
    assert "加分项" not in out
    assert "面试侧重" not in out


def test_format_profile_full():
    data = {
        "company": "华为",
        "position": "AI应用开发",
        "difficulty_tendency": "senior",
        "focus_areas": ["分布式", "算法"],
        "interview_style": "系统设计为主",
        "question_types": ["开放题", "场景题"],
        "key_traits": ["抗压"],
        "source_count": 12,
    }
    out = format_profile(data)
    assert "公司：华为 / 岗位：AI应用开发" in out
    assert "难度倾向：高级" in out
    assert "考查重点：分布式, 算法" in out
    assert "面试风格：系统设计为主" in out
    assert "常见问题类型：开放题, 场景题" in out
    assert "区分性特征：抗压" in out
    assert "（基于12份面经分析）" in out


def test_format_profile_empty():
    assert format_profile({}) == ""


def test_format_profile_difficulty_labels():
    assert "难度倾向：初级" in format_profile({"difficulty_tendency": "junior"})
    assert "难度倾向：中级" in format_profile({"difficulty_tendency": "mid"})
    assert "难度倾向：高级" in format_profile({"difficulty_tendency": "senior"})


async def test_fetch_profile_mock_success(monkeypatch):
    payload = {
        "company": "Acme",
        "position": "Eng",
        "difficulty_tendency": "mid",
    }

    class _FakeResp:
        status_code = 200

        def json(self):
            return payload

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            return _FakeResp()

    monkeypatch.setattr("interview_tester.utils.httpx.AsyncClient", _FakeClient)

    out = await fetch_profile("Acme", "Eng")
    assert "公司：Acme / 岗位：Eng" in out
    assert "难度倾向：中级" in out


async def test_fetch_profile_mock_failure(monkeypatch):
    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            raise RuntimeError("boom")

    monkeypatch.setattr("interview_tester.utils.httpx.AsyncClient", _FakeClient)

    out = await fetch_profile("Acme", "Eng")
    assert out == ""


async def test_fetch_profile_empty_company():
    assert await fetch_profile("", "Eng") == ""
    assert await fetch_profile("Acme", "") == ""
