from __future__ import annotations

from pathlib import Path
from typing import Iterable


SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__", ".venv", "build", "dist"}


def _guess_language(path: Path) -> str:
    ext = path.suffix.lower()
    mapping = {
        ".py": "python",
        ".md": "markdown",
        ".json": "json",
        ".toml": "toml",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".sh": "shell",
        ".yaml": "yaml",
        ".yml": "yaml",
    }

    return mapping.get(ext, ext.lstrip(".") or "binary")


def scan_project(root: Path | str, *, max_files: int = 2000) -> list[dict]:
    """Scan a project directory and return a list of file metadata dicts.

    Each entry contains: path (relative), size, language, snippet (first lines).
    """
    root_p = Path(root)

    if not root_p.exists() or not root_p.is_dir():
        return []

    results: list[dict] = []
    count = 0

    for path in sorted(root_p.rglob("*")):
        if count >= max_files:
            break

        try:
            rel_parts = path.relative_to(root_p).parts
        except Exception:
            continue

        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        if path.is_file():
            try:
                size = path.stat().st_size
            except Exception:
                size = 0

            lang = _guess_language(path)

            snippet = ""
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as fh:
                    lines = []
                    for _ in range(5):
                        line = fh.readline()
                        if not line:
                            break
                        lines.append(line.rstrip("\n"))
                    snippet = "\n".join(lines)
            except Exception:
                snippet = "(binary or unreadable)"

            results.append(
                {
                    "path": str(path.relative_to(root_p)),
                    "size": size,
                    "language": lang,
                    "snippet": snippet,
                }
            )

            count += 1

    return results


def scan_many(roots: Iterable[Path | str], **kwargs) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in roots:
        out[str(r)] = scan_project(r, **kwargs)
    return out
