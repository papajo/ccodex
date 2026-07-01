from __future__ import annotations

from dataclasses import dataclass, field


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
