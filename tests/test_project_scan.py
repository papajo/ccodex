from pathlib import Path

from engine.project import scan_project


def test_scan_project(tmp_path):
    (tmp_path / "a.py").write_text("print('a')\n")
    (tmp_path / "README.md").write_text("# title\n")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "b.txt").write_text("hello\n")

    results = scan_project(tmp_path)

    paths = {r["path"] for r in results}

    assert "a.py" in paths
    assert "README.md" in paths
    assert "subdir/b.txt" in paths
