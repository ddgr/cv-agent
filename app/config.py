import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    agent_api_key: str
    model: str
    cv_path: Path
    max_output_tokens: int
    request_timeout_s: float


def load_settings() -> Settings:
    settings = Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        agent_api_key=os.environ.get("AGENT_API_KEY", ""),
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        cv_path=Path(os.environ.get("CV_PATH", "knowledge/cv.md")),
        max_output_tokens=int(os.environ.get("MAX_OUTPUT_TOKENS", "2048")),
        request_timeout_s=float(os.environ.get("REQUEST_TIMEOUT_S", "30")),
    )
    if not settings.anthropic_api_key or not settings.agent_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY and AGENT_API_KEY must be set")
    return settings
