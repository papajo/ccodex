from pathlib import Path

from engine.commands import handle_command
from engine.config import Config
from engine.history import ChatHistory


class DummyClient:
    def __init__(self):
        self.stats = None


def make_env():
    return Config(
        base_url="http://localhost:8001/v1",
        model="test",
        api_key="",
        temperature=0.2,
        max_tokens=100,
        timeout=10.0,
        history_limit=10,
        system_prompt_path=Path("system.md"),
        config_path=Path("config.toml"),
        config_loaded=False,
    )


def test_write_returns_interactive():
    cfg = make_env()
    hist = ChatHistory(limit=5)
    client = DummyClient()

    res = handle_command("/write newfile.txt", history=hist, config=cfg, client=client)

    assert res.handled
    assert res.interactive is not None
    assert res.interactive.get("type") == "collect_multiline"
    assert res.interactive.get("path") == "newfile.txt"


def test_write_rejects_bad_path():
    cfg = make_env()
    hist = ChatHistory(limit=5)
    client = DummyClient()

    res = handle_command("/write ../secrets.txt", history=hist, config=cfg, client=client)
    assert res.handled
    assert "only accepts safe relative paths" in (res.output or "")
