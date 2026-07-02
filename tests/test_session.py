from pathlib import Path

from engine.history import ChatHistory


def test_session_save_load(tmp_path):
    hist = ChatHistory(limit=5)
    hist.add_user("hello")
    hist.add_assistant("hi")

    session_file = tmp_path / "sess.json"
    hist.save(session_file)

    loaded = ChatHistory.load(session_file, limit=5)

    assert len(loaded.messages) == 2
    assert loaded.messages[0]["content"] == "hello"
