from interview_tester.schemas import Evaluation, QAPair, TestConfig, TestSession


def test_qa_pair_creation():
    qa = QAPair(
        round=3,
        question="What is REST?",
        answer="An architectural style.",
        question_timestamp="2024-01-01T00:00:00+00:00",
        answer_timestamp="2024-01-01T00:00:10+00:00",
    )
    assert qa.round == 3
    assert qa.question == "What is REST?"
    assert qa.answer == "An architectural style."
    assert qa.question_timestamp == "2024-01-01T00:00:00+00:00"
    assert qa.answer_timestamp == "2024-01-01T00:00:10+00:00"


def test_test_config_defaults():
    cfg = TestConfig()
    assert cfg.domain == "backend"
    assert cfg.difficulty == "mid"
    assert cfg.candidate_level == "mid"
    assert cfg.max_rounds == 50
    assert cfg.job_description == ""
    assert cfg.profile_company == ""
    assert cfg.profile_position == ""
    assert cfg.provider == ""
    assert cfg.candidate_style == "cooperative"
    assert cfg.candidate_weaknesses == []


def test_test_config_with_data():
    cfg = TestConfig(
        domain="frontend",
        difficulty="senior",
        candidate_level="junior",
        max_rounds=10,
        job_description="JD text",
        profile_company="Acme",
        profile_position="Engineer",
        provider="openai",
        candidate_style="weak",
        candidate_weaknesses=["sql", "k8s"],
    )
    assert cfg.domain == "frontend"
    assert cfg.difficulty == "senior"
    assert cfg.candidate_level == "junior"
    assert cfg.max_rounds == 10
    assert cfg.job_description == "JD text"
    assert cfg.profile_company == "Acme"
    assert cfg.profile_position == "Engineer"
    assert cfg.provider == "openai"
    assert cfg.candidate_style == "weak"
    assert cfg.candidate_weaknesses == ["sql", "k8s"]


def test_evaluation_creation():
    ev = Evaluation(
        style_naturalness=8,
        difficulty_appropriateness=7,
        follow_up_quality=6,
        topic_coverage=9,
        overall_score=7,
        strengths=["good"],
        weaknesses=["bad"],
        summary="ok",
        improvement_suggestions=["sug"],
    )
    assert ev.style_naturalness == 8
    assert ev.difficulty_appropriateness == 7
    assert ev.follow_up_quality == 6
    assert ev.topic_coverage == 9
    assert ev.overall_score == 7
    assert ev.strengths == ["good"]
    assert ev.weaknesses == ["bad"]
    assert ev.summary == "ok"
    assert ev.improvement_suggestions == ["sug"]


def test_evaluation_defaults():
    ev = Evaluation(
        style_naturalness=1,
        difficulty_appropriateness=1,
        follow_up_quality=1,
        topic_coverage=1,
        overall_score=1,
        strengths=[],
        weaknesses=[],
        summary="",
        improvement_suggestions=[],
    )
    assert ev.jd_relevance == 0
    assert ev.profile_relevance == 0
    assert ev.difficulty_adaptation == 0


def test_test_session_creation():
    cfg = TestConfig()
    session = TestSession(
        session_id="sid",
        config=cfg,
        started_at="2024-01-01T00:00:00+00:00",
    )
    assert session.session_id == "sid"
    assert session.config is cfg
    assert session.started_at == "2024-01-01T00:00:00+00:00"


def test_test_session_defaults():
    session = TestSession(
        session_id="sid",
        config=TestConfig(),
        started_at="2024-01-01T00:00:00+00:00",
    )
    assert session.qa_pairs == []
    assert session.evaluation is None
    assert session.status == "running"
    assert session.ended_at == ""
    assert session.total_rounds == 0
