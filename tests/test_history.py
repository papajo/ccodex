from pathlib import Path
import json
import tempfile

from engine.history import ChatHistory


def test_save_and_load_history(tmp_path: Path) -> None:
    hist = ChatHistory(limit=5)
    hist.add_user("hello")
    hist.add_assistant("hi there")

    file = tmp_path / "history.json"
    hist.save(file)

    assert file.exists()

    loaded = ChatHistory.load(file, limit=5)
    assert loaded.turns == hist.turns
    assert loaded.messages == hist.messages
