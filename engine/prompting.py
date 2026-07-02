from __future__ import annotations

from engine.config import Config


DEFAULT_FALLBACK_PROMPT = "You are ccodex, a concise and careful coding assistant."


def read_system_prompt(config: Config) -> str:
    if not config.system_prompt_path.exists():
        return DEFAULT_FALLBACK_PROMPT

    return config.system_prompt_path.read_text(encoding="utf-8").strip()


def build_system_prompt(config: Config) -> str:
    base_prompt = read_system_prompt(config)

    runtime_context = f"""
Runtime metadata:
- Assistant name: ccodex
- Active model: {config.model}
- API base URL: {config.base_url}

If the user asks what model is running, answer using the active model from this runtime metadata.
""".strip()

    return f"{base_prompt}\n\n{runtime_context}"