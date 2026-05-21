from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_INTERVIEW_AGENT_ENV = Path(__file__).resolve().parent.parent.parent.parent / "interview-agent" / ".env"


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TEST_",
        env_file=str(_INTERVIEW_AGENT_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "sessions"
    candidate_temperature: float = 0.7
    evaluator_temperature: float = 0.3


test_settings = TestSettings()
