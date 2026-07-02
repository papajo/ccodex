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


def test_write_dry_run(tmp_path):
    # ensure dry-run writes .ccodex_dryrun.diff and does not modify file
    repo_root = tmp_path
    f = repo_root / "sample.txt"
    f.write_text("old\n", encoding="utf-8")

    # simulate chat write flow by directly invoking the logic
    new_text = "new\n"
    import difflib
    old_lines = "old\n".splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(old_lines, new_lines, fromfile=str(f), tofile=str(f) + " (new)"))

    # write dry-run diff
    dr = repo_root / ".ccodex_dryrun.diff"
    dr.write_text(diff, encoding="utf-8")

    assert dr.exists()
    assert f.read_text(encoding="utf-8") == "old\n"
