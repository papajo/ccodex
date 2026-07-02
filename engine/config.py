from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_SYSTEM_PROMPT = Path(__file__).resolve().parent / "prompts" / "system.md"
DEFAULT_CONFIG_PATH = Path("config.toml")


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
    config_path: Path
    config_loaded: bool


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("rb") as file:
        data = tomllib.load(file)

    if not isinstance(data, dict):
        return {}

    return data


def _config_path() -> Path:
    raw = os.getenv("CCODEX_CONFIG")

    if raw:
        return Path(raw).expanduser()

    return DEFAULT_CONFIG_PATH


def _get_value(
    *,
    toml_data: dict[str, Any],
    key: str,
    env_name: str,
    default: Any,
) -> Any:
    env_value = os.getenv(env_name)

    if env_value is not None:
        return env_value

    if key in toml_data:
        return toml_data[key]

    return default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_path(value: Any, default: Path) -> Path:
    if value is None:
        return default

    return Path(str(value)).expanduser()


def load_config() -> Config:
    config_path = _config_path()
    toml_data = _read_toml(config_path)
    config_loaded = bool(toml_data)

    base_url = str(
        _get_value(
            toml_data=toml_data,
            key="base_url",
            env_name="CCODEX_BASE_URL",
            default="http://localhost:8001/v1",
        )
    ).rstrip("/")

    model = str(
        _get_value(
            toml_data=toml_data,
            key="model",
            env_name="CCODEX_MODEL",
            default="Ornith-1.0-9B-4bit",
        )
    )

    api_key = str(
        _get_value(
            toml_data=toml_data,
            key="api_key",
            env_name="CCODEX_API_KEY",
            default="",
        )
    )

    temperature = _as_float(
        _get_value(
            toml_data=toml_data,
            key="temperature",
            env_name="CCODEX_TEMPERATURE",
            default=0.2,
        ),
        0.2,
    )

    max_tokens = _as_int(
        _get_value(
            toml_data=toml_data,
            key="max_tokens",
            env_name="CCODEX_MAX_TOKENS",
            default=2048,
        ),
        2048,
    )

    timeout = _as_float(
        _get_value(
            toml_data=toml_data,
            key="timeout",
            env_name="CCODEX_TIMEOUT",
            default=120.0,
        ),
        120.0,
    )

    history_limit = _as_int(
        _get_value(
            toml_data=toml_data,
            key="history_limit",
            env_name="CCODEX_HISTORY_LIMIT",
            default=20,
        ),
        20,
    )

    system_prompt_path = _as_path(
        _get_value(
            toml_data=toml_data,
            key="system_prompt",
            env_name="CCODEX_SYSTEM_PROMPT",
            default=DEFAULT_SYSTEM_PROMPT,
        ),
        DEFAULT_SYSTEM_PROMPT,
    )

    return Config(
        base_url=base_url,
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        history_limit=history_limit,
        system_prompt_path=system_prompt_path,
        config_path=config_path,
        config_loaded=config_loaded,
    )