from __future__ import annotations

from dataclasses import dataclass

from engine.client import OpenAICompatibleClient
from engine.config import Config
from engine.history import ChatHistory


HELP_TEXT = """
ccodex commands

/help       Show this help message
/clear      Clear conversation history
/history    Show current conversation history
/stats      Show local runtime stats
/exit       Exit ccodex
/quit       Exit ccodex

Anything else is sent to the model.
""".strip()


@dataclass
class CommandResult:
    handled: bool
    should_exit: bool = False
    output: str | None = None


def handle_command(
    raw: str,
    *,
    history: ChatHistory,
    config: Config,
    client: OpenAICompatibleClient,
) -> CommandResult:
    text = raw.strip()

    if not text.startswith("/"):
        return CommandResult(handled=False)

    command = text.split()[0].lower()

    if command in {"/exit", "/quit"}:
        return CommandResult(handled=True, should_exit=True, output="bye.")

    if command == "/help":
        return CommandResult(handled=True, output=HELP_TEXT)

    if command == "/clear":
        history.clear()
        return CommandResult(handled=True, output="Conversation history cleared.")

    if command == "/history":
        return CommandResult(handled=True, output=history.format_history())

    if command == "/stats":
        latency = client.stats.last_latency_seconds
        latency_text = "n/a" if latency is None else f"{latency:.2f}s"
        error_text = client.stats.last_error or "none"

        output = f"""
Runtime stats

Base URL:      {config.base_url}
Model:         {config.model}
Temperature:   {config.temperature}
Max tokens:    {config.max_tokens}
History turns: {history.turns}
Requests:      {client.stats.requests}
Last latency:  {latency_text}
Last chars:    {client.stats.last_chars}
Last error:    {error_text}
""".strip()

        return CommandResult(handled=True, output=output)

    return CommandResult(
        handled=True,
        output=f"Unknown command: {command}\nType /help for available commands.",
    )
