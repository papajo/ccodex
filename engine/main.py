from __future__ import annotations

from engine.chat import run_chat
from engine.config import load_config


def main() -> None:
    config = load_config()
    run_chat(config)
