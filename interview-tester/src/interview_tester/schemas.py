from pydantic import BaseModel


class QAPair(BaseModel):
    round: int
    question: str
    answer: str
    question_timestamp: str
    answer_timestamp: str


class TestConfig(BaseModel):
    domain: str = "backend"
    difficulty: str = "mid"
    candidate_level: str = "mid"
    max_rounds: int = 50
    job_description: str = ""
    profile_company: str = ""
    profile_position: str = ""
    provider: str = ""
    candidate_style: str = "cooperative"
    candidate_weaknesses: list[str] = []


class Evaluation(BaseModel):
    style_naturalness: int
    difficulty_appropriateness: int
    follow_up_quality: int
    topic_coverage: int
    overall_score: int
    strengths: list[str]
    weaknesses: list[str]
    summary: str
    improvement_suggestions: list[str]
    jd_relevance: int = 0           # 0=未使用JD or no JD provided, 1-10=JD使用相关度
    profile_relevance: int = 0      # 0=未使用Profile or no Profile provided, 1-10=Profile匹配度
    difficulty_adaptation: int = 0  # 0=无动态调整, 1-10=动态调整能力


class TestSession(BaseModel):
    session_id: str
    config: TestConfig
    started_at: str
    ended_at: str = ""
    qa_pairs: list[QAPair] = []
    evaluation: Evaluation | None = None
    total_rounds: int = 0
    status: str = "running"
