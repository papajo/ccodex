from pathlib import Path

from engine.commands import handle_command
from engine.config import Config
from engine.history import ChatHistory


class DummyClient:
    def __init__(self):
        self.stats = None


def test_read_file(tmp_path):
    file = tmp_path / "sample.txt"
    content = "hello world\nthis is a test\n"
    file.write_text(content, encoding="utf-8")

    # change cwd to tmp_path for the duration of the test
    old_cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)

        config = Config(
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

        history = ChatHistory(limit=5)
        client = DummyClient()

        result = handle_command(f"/read {file.name}", history=history, config=config, client=client)

        assert result.handled
        assert "hello world" in (result.output or "")

    finally:
        os.chdir(old_cwd)
