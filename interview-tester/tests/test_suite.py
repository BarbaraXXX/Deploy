
import yaml

from interview_tester.schemas import Evaluation, TestConfig, TestSession
from interview_tester.suite import (
    MatrixConfig,
    SuiteTestConfig,
    TestSuite,
    compute_summary,
    expand_matrix,
    load_suite,
    resolve_suite,
    suite_test_config_to_test_config,
)


def _session(
    session_id: str,
    *,
    domain: str = "backend",
    difficulty: str = "mid",
    candidate_style: str = "cooperative",
    overall: int = 7,
    status: str = "completed",
    with_eval: bool = True,
) -> TestSession:
    cfg = TestConfig(domain=domain, difficulty=difficulty, candidate_style=candidate_style)
    ev = None
    if with_eval:
        ev = Evaluation(
            style_naturalness=overall,
            difficulty_appropriateness=overall,
            follow_up_quality=overall,
            topic_coverage=overall,
            overall_score=overall,
            strengths=[],
            weaknesses=[],
            summary="",
            improvement_suggestions=[],
            jd_relevance=0,
            profile_relevance=0,
            difficulty_adaptation=overall,
        )
    return TestSession(
        session_id=session_id,
        config=cfg,
        started_at="2024-01-01T00:00:00+00:00",
        status=status,
        evaluation=ev,
    )


def test_expand_matrix_single_domain():
    matrix = MatrixConfig(domains=["backend"])
    configs = expand_matrix(matrix)
    assert len(configs) == 1
    assert configs[0].domain == "backend"


def test_expand_matrix_multiple_domains():
    matrix = MatrixConfig(
        domains=["backend", "frontend", "algorithm"],
        candidate_styles=["cooperative", "weak"],
    )
    configs = expand_matrix(matrix)
    assert len(configs) == 6


def test_expand_matrix_full():
    matrix = MatrixConfig(
        domains=["a", "b"],
        difficulties=["junior", "mid"],
        candidate_levels=["mid", "senior"],
        candidate_styles=["cooperative", "weak"],
    )
    configs = expand_matrix(matrix)
    assert len(configs) == 2 * 2 * 2 * 2


def test_expand_matrix_empty_uses_base():
    base = SuiteTestConfig(
        domain="X",
        difficulty="senior",
        candidate_level="junior",
        candidate_style="evasive",
    )
    matrix = MatrixConfig(base=base)
    configs = expand_matrix(matrix)
    assert len(configs) == 1
    cfg = configs[0]
    assert cfg.domain == "X"
    assert cfg.difficulty == "senior"
    assert cfg.candidate_level == "junior"
    assert cfg.candidate_style == "evasive"


def test_load_suite_valid(tmp_path):
    yaml_data = {
        "name": "my_suite",
        "description": "desc",
        "pass_threshold": 6,
        "tests": [
            {"domain": "backend", "difficulty": "mid"},
        ],
        "matrix": {
            "domains": ["frontend"],
            "candidate_styles": ["weak"],
        },
    }
    path = tmp_path / "suite.yaml"
    path.write_text(yaml.safe_dump(yaml_data), encoding="utf-8")
    suite = load_suite(path)
    assert suite.name == "my_suite"
    assert suite.description == "desc"
    assert suite.pass_threshold == 6
    assert len(suite.tests) == 1
    assert suite.matrix is not None
    assert suite.matrix.domains == ["frontend"]


def test_load_suite_minimal(tmp_path):
    path = tmp_path / "min.yaml"
    path.write_text(yaml.safe_dump({"name": "tiny"}), encoding="utf-8")
    suite = load_suite(path)
    assert suite.name == "tiny"
    assert suite.tests == []
    assert suite.matrix is None
    assert suite.pass_threshold == 7


def test_resolve_suite_tests_only():
    suite = TestSuite(
        name="t",
        tests=[SuiteTestConfig(domain="backend"), SuiteTestConfig(domain="frontend")],
    )
    out = resolve_suite(suite)
    assert len(out) == 2
    assert [c.domain for c in out] == ["backend", "frontend"]


def test_resolve_suite_matrix_only():
    suite = TestSuite(
        name="t",
        matrix=MatrixConfig(domains=["a", "b", "c"]),
    )
    out = resolve_suite(suite)
    assert len(out) == 3


def test_resolve_suite_both():
    suite = TestSuite(
        name="t",
        tests=[SuiteTestConfig(domain="x")],
        matrix=MatrixConfig(domains=["a", "b"]),
    )
    out = resolve_suite(suite)
    assert len(out) == 3
    assert out[0].domain == "x"


def test_suite_test_config_to_test_config():
    stc = SuiteTestConfig(
        domain="game",
        difficulty="senior",
        candidate_level="junior",
        candidate_style="weak",
        candidate_weaknesses=["sql"],
        max_rounds=20,
        job_description="jd",
        profile_company="c",
        profile_position="p",
        provider="prov",
    )
    cfg = suite_test_config_to_test_config(stc)
    assert isinstance(cfg, TestConfig)
    assert cfg.domain == "game"
    assert cfg.difficulty == "senior"
    assert cfg.candidate_level == "junior"
    assert cfg.candidate_style == "weak"
    assert cfg.candidate_weaknesses == ["sql"]
    assert cfg.max_rounds == 20
    assert cfg.job_description == "jd"
    assert cfg.profile_company == "c"
    assert cfg.profile_position == "p"
    assert cfg.provider == "prov"


def test_compute_summary_basic():
    suite = TestSuite(name="s", pass_threshold=7)
    sessions = [_session("a", overall=8), _session("b", overall=7), _session("c", overall=6)]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert summary.total_tests == 3
    assert summary.completed == 3
    assert summary.errors == 0
    assert summary.pass_count == 2
    assert summary.fail_count == 1
    assert summary.pass_rate == 0.67


def test_compute_summary_mixed():
    suite = TestSuite(name="s", pass_threshold=7)
    sessions = [
        _session("a", overall=8),
        _session("b", status="error", with_eval=False),
        _session("c", overall=9),
    ]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert summary.total_tests == 3
    assert summary.completed == 2
    assert summary.errors == 1
    assert summary.pass_count == 2


def test_compute_summary_all_errors():
    suite = TestSuite(name="s", pass_threshold=7)
    sessions = [
        _session("a", status="error", with_eval=False),
        _session("b", status="error", with_eval=False),
    ]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert summary.completed == 0
    assert summary.errors == 2
    assert summary.pass_rate == 0.0
    assert summary.pass_count == 0
    assert summary.best_session is None
    assert summary.worst_session is None


def test_compute_summary_pass_fail():
    suite = TestSuite(name="s", pass_threshold=7)
    sessions = [_session(f"s{i}", overall=score) for i, score in enumerate([9, 8, 5, 4])]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert summary.pass_count == 2
    assert summary.fail_count == 2


def test_compute_summary_best_worst():
    suite = TestSuite(name="s")
    sessions = [
        _session("low", overall=3),
        _session("hi", overall=10),
        _session("mid", overall=6),
    ]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert summary.best_session == "hi"
    assert summary.worst_session == "low"


def test_compute_summary_group_by_domain():
    suite = TestSuite(name="s", pass_threshold=7)
    sessions = [
        _session("a", domain="backend", overall=8),
        _session("b", domain="backend", overall=6),
        _session("c", domain="frontend", overall=9),
    ]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert "backend" in summary.by_domain
    assert "frontend" in summary.by_domain
    assert summary.by_domain["backend"]["count"] == 2
    assert summary.by_domain["backend"]["pass_rate"] == 0.5
    assert summary.by_domain["frontend"]["count"] == 1
    assert summary.by_domain["frontend"]["pass_rate"] == 1.0


def test_compute_summary_group_by_style():
    suite = TestSuite(name="s", pass_threshold=7)
    sessions = [
        _session("a", candidate_style="cooperative", overall=8),
        _session("b", candidate_style="weak", overall=5),
        _session("c", candidate_style="weak", overall=9),
    ]
    summary = compute_summary(suite, sessions, "2024-01-01T00:00:00+00:00")
    assert summary.by_candidate_style["cooperative"]["count"] == 1
    assert summary.by_candidate_style["cooperative"]["pass_rate"] == 1.0
    assert summary.by_candidate_style["weak"]["count"] == 2
    assert summary.by_candidate_style["weak"]["pass_rate"] == 0.5
