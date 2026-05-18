import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class LLMProviderConfig:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_provider: str = "local"
    providers: str = '{}'

    @field_validator("providers", mode="before")
    @classmethod
    def _coerce_empty_providers(cls, v: str) -> str:
        return v if v.strip() else '{}'

    def get_providers(self) -> dict[str, LLMProviderConfig]:
        raw = json.loads(self.providers)
        result = {}
        for name, cfg in raw.items():
            result[name] = LLMProviderConfig(
                base_url=cfg.get("base_url", "http://localhost:11434/v1"),
                api_key=cfg.get("api_key", "not-needed") or "not-needed",
                model=cfg.get("model", ""),
            )
        return result

    def get_provider(self, name: str | None = None) -> LLMProviderConfig:
        providers = self.get_providers()
        provider_name = name or self.default_provider
        if provider_name in providers:
            return providers[provider_name]
        if providers:
            return next(iter(providers.values()))
        return LLMProviderConfig(
            base_url="http://localhost:11434/v1",
            api_key="not-needed",
            model="qwen2.5:7b",
        )


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_urls: str = ""
    stdio_command: str = ""
    stdio_args: str = ""


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = "change-me-in-production"
    token_expire_hours: int = 24


llm_settings = LLMSettings()
mcp_settings = MCPSettings()
auth_settings = AuthSettings()
