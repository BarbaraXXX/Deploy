"""Test suite system for batch execution and result aggregation."""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel

from .schemas import TestConfig, TestSession

logger = logging.getLogger(__name__)


class SuiteTestConfig(BaseModel):
    """A single test within a suite. Maps to TestConfig with optional overrides."""

    domain: str = "backend"
    difficulty: str = "mid"
    candidate_level: str = "mid"
    candidate_style: str = "cooperative"
    candidate_weaknesses: list[str] = []
    max_rounds: int = 50
    job_description: str = ""
    profile_company: str = ""
    profile_position: str = ""
    provider: str = ""


class MatrixConfig(BaseModel):
    """Matrix expansion config - generates tests from combinations."""

    domains: list[str] = []
    difficulties: list[str] = []
    candidate_levels: list[str] = []
    candidate_styles: list[str] = []
    base: SuiteTestConfig = SuiteTestConfig()


class TestSuite(BaseModel):
    """A test suite definition."""

    name: str
    description: str = ""
    tests: list[SuiteTestConfig] = []
    matrix: MatrixConfig | None = None
    pass_threshold: int = 7


class SuiteSummary(BaseModel):
    """Aggregated results from a suite run."""

    suite_name: str
    total_tests: int
    completed: int
    errors: int
    pass_count: int
    fail_count: int
    pass_rate: float
    avg_overall_score: float
    avg_style_naturalness: float
    avg_difficulty_appropriateness: float
    avg_follow_up_quality: float
    avg_topic_coverage: float
    avg_jd_relevance: float
    avg_profile_relevance: float
    avg_difficulty_adaptation: float
    by_domain: dict[str, dict]
    by_difficulty: dict[str, dict]
    by_candidate_style: dict[str, dict]
    best_session: str | None = None
    worst_session: str | None = None
    started_at: str
    ended_at: str = ""


def expand_matrix(matrix: MatrixConfig) -> list[SuiteTestConfig]:
    """Expand a matrix config into individual test configs via Cartesian product."""
    configs: list[SuiteTestConfig] = []
    domains = matrix.domains or [matrix.base.domain]
    difficulties = matrix.difficulties or [matrix.base.difficulty]
    levels = matrix.candidate_levels or [matrix.base.candidate_level]
    styles = matrix.candidate_styles or [matrix.base.candidate_style]

    for domain in domains:
        for difficulty in difficulties:
            for level in levels:
                for style in styles:
                    cfg = matrix.base.model_copy(update={
                        "domain": domain,
                        "difficulty": difficulty,
                        "candidate_level": level,
                        "candidate_style": style,
                    })
                    configs.append(cfg)
    logger.info(
        "expand_matrix: produced %d configs (domains=%d, difficulties=%d, levels=%d, styles=%d)",
        len(configs), len(domains), len(difficulties), len(levels), len(styles),
    )
    return configs


def load_suite(path: Path) -> TestSuite:
    """Load a test suite from a YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tests_data = data.get("tests", [])
    tests = [SuiteTestConfig(**t) for t in tests_data]

    matrix_data = data.get("matrix")
    matrix = MatrixConfig(**matrix_data) if matrix_data else None

    suite = TestSuite(
        name=data.get("name", "unnamed"),
        description=data.get("description", ""),
        tests=tests,
        matrix=matrix,
        pass_threshold=data.get("pass_threshold", 7),
    )
    logger.info(
        "load_suite: loaded %r from %s (tests=%d, has_matrix=%s, pass_threshold=%d)",
        suite.name, path, len(suite.tests), suite.matrix is not None, suite.pass_threshold,
    )
    return suite


def resolve_suite(suite: TestSuite) -> list[SuiteTestConfig]:
    """Resolve a suite into a flat list of test configs (expanding matrix if present)."""
    configs = list(suite.tests)
    if suite.matrix:
        configs.extend(expand_matrix(suite.matrix))
    return configs


def suite_test_config_to_test_config(stc: SuiteTestConfig) -> TestConfig:
    """Convert SuiteTestConfig to TestConfig."""
    return TestConfig(
        domain=stc.domain,
        difficulty=stc.difficulty,
        candidate_level=stc.candidate_level,
        candidate_style=stc.candidate_style,
        candidate_weaknesses=stc.candidate_weaknesses,
        max_rounds=stc.max_rounds,
        job_description=stc.job_description,
        profile_company=stc.profile_company,
        profile_position=stc.profile_position,
        provider=stc.provider,
    )


def compute_summary(
    suite: TestSuite,
    sessions: list[TestSession],
    started_at: str,
) -> SuiteSummary:
    """Compute aggregated summary from suite run results."""
    completed = [s for s in sessions if s.status == "completed" and s.evaluation]
    errors = len(sessions) - len(completed)

    pass_count = sum(
        1 for s in completed
        if s.evaluation and s.evaluation.overall_score >= suite.pass_threshold
    )
    fail_count = len(completed) - pass_count
    pass_rate = round(pass_count / len(completed), 2) if completed else 0.0

    def _avg(field: str) -> float:
        vals = [getattr(s.evaluation, field) for s in completed if s.evaluation]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def _group_by(key: str) -> dict[str, dict]:
        groups: dict[str, list[TestSession]] = {}
        for s in completed:
            k = str(getattr(s.config, key, "unknown"))
            groups.setdefault(k, []).append(s)
        result: dict[str, dict] = {}
        for k, group in groups.items():
            scores = [s.evaluation.overall_score for s in group if s.evaluation]
            p = sum(1 for sc in scores if sc >= suite.pass_threshold)
            result[k] = {
                "count": len(group),
                "pass_rate": round(p / len(group), 2) if group else 0.0,
                "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
            }
        return result

    best = max(completed, key=lambda s: s.evaluation.overall_score) if completed else None
    worst = min(completed, key=lambda s: s.evaluation.overall_score) if completed else None

    return SuiteSummary(
        suite_name=suite.name,
        total_tests=len(sessions),
        completed=len(completed),
        errors=errors,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=pass_rate,
        avg_overall_score=_avg("overall_score"),
        avg_style_naturalness=_avg("style_naturalness"),
        avg_difficulty_appropriateness=_avg("difficulty_appropriateness"),
        avg_follow_up_quality=_avg("follow_up_quality"),
        avg_topic_coverage=_avg("topic_coverage"),
        avg_jd_relevance=_avg("jd_relevance"),
        avg_profile_relevance=_avg("profile_relevance"),
        avg_difficulty_adaptation=_avg("difficulty_adaptation"),
        by_domain=_group_by("domain"),
        by_difficulty=_group_by("difficulty"),
        by_candidate_style=_group_by("candidate_style"),
        best_session=best.session_id if best else None,
        worst_session=worst.session_id if worst else None,
        started_at=started_at,
    )
