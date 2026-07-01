from __future__ import annotations

from engine.config import Config


DEFAULT_FALLBACK_PROMPT = "You are ccodex, a concise and careful coding assistant."


def read_system_prompt(config: Config) -> str:
    if not config.system_prompt_path.exists():
        return DEFAULT_FALLBACK_PROMPT

    return config.system_prompt_path.read_text(encoding="utf-8").strip()