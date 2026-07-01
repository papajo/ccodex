from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SYSTEM_PROMPT = Path(__file__).resolve().parent / "prompts" / "system.md"


@dataclass(frozen=True)
class Config:
    base_url: str
    model: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout: float
    history_limit: int
    system_prompt_path: Path


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def load_config() -> Config:
    return Config(
        base_url=os.getenv("CCODEX_BASE_URL", "http://localhost:8001/v1").rstrip("/"),
        model=os.getenv("CCODEX_MODEL", "Ornith-1.0-9B-4bit"),
        api_key=os.getenv("CCODEX_API_KEY", "local-not-needed"),
        temperature=_float_env("CCODEX_TEMPERATURE", 0.2),
        max_tokens=_int_env("CCODEX_MAX_TOKENS", 2048),
        timeout=_float_env("CCODEX_TIMEOUT", 120.0),
        history_limit=_int_env("CCODEX_HISTORY_LIMIT", 20),
        system_prompt_path=Path(
            os.getenv("CCODEX_SYSTEM_PROMPT", str(DEFAULT_SYSTEM_PROMPT))
        ),
    )
