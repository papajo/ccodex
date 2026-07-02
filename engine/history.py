from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


Message = dict[str, str]


@dataclass
class ChatHistory:
    limit: int = 20
    messages: list[Message] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self.trim()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self.trim()

    def clear(self) -> None:
        self.messages.clear()

    def trim(self) -> None:
        if self.limit <= 0:
            self.messages.clear()
            return

        max_messages = self.limit * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def remove_last(self) -> None:
        if self.messages:
            self.messages.pop()

    def to_messages(self, system_prompt: str) -> list[Message]:
        return [{"role": "system", "content": system_prompt}, *self.messages]

    def format_history(self) -> str:
        if not self.messages:
            return "No conversation history yet."

        lines: list[str] = []
        for idx, msg in enumerate(self.messages, start=1):
            role = msg["role"]
            content = msg["content"].strip()
            lines.append(f"{idx}. {role}: {content}")
        return "\n".join(lines)

    @property
    def turns(self) -> int:
        return sum(1 for msg in self.messages if msg["role"] == "user")

    # Persistence helpers
    def to_dict(self) -> dict:
        return {"limit": self.limit, "messages": list(self.messages)}

    @classmethod
    def from_dict(cls, data: dict) -> "ChatHistory":
        limit = int(data.get("limit", 20))
        msgs = list(data.get("messages", []))
        h = cls(limit=limit)
        h.messages = msgs
        h.trim()
        return h

    def save(self, path: str | Path) -> None:
        import json
        from pathlib import Path

        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # non-fatal
            return

    @classmethod
    def load(cls, path: str | Path, limit: int | None = None) -> "ChatHistory":
        import json
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            return cls(limit=limit or 20)

        try:
            raw = p.read_text(encoding="utf-8")
            data = json.loads(raw)
            hist = cls.from_dict(data)
            if limit is not None:
                hist.limit = limit
                hist.trim()
            return hist
        except Exception:
            return cls(limit=limit or 20)

    # Persistence helpers
    def to_dict(self) -> dict[str, Any]:
        return {"limit": self.limit, "messages": self.messages}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatHistory":
        limit = int(data.get("limit", 20))
        messages = data.get("messages", []) or []
        return cls(limit=limit, messages=list(messages))

    def save(self, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                json.dump(self.to_dict(), fh, ensure_ascii=False, indent=2)
        except Exception:
            # Best-effort save; do not raise to avoid disrupting CLI shutdown
            return

    @classmethod
    def load(cls, path: Path, limit: int = 20) -> "ChatHistory":
        if not path.exists():
            return cls(limit=limit)

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)

            hist = cls.from_dict(data)
            hist.limit = limit
            hist.trim()
            return hist
        except Exception:
            # If loading fails, return empty history
            return cls(limit=limit)
