from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = "http://localhost:11434/v1"
    api_key: str = "not-needed"
    model: str = "qwen2.5:7b"

    @field_validator("api_key", mode="before")
    @classmethod
    def _coerce_empty_key(cls, v: str) -> str:
        return v if v.strip() else "not-needed"


class MCPServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    port: int = 9000


llm_settings = LLMSettings()
mcp_server_settings = MCPServerSettings()
