from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib

from engine.client import OpenAICompatibleClient
from engine.config import Config
from engine.history import ChatHistory
from engine.prompting import build_system_prompt
import json

HELP_TEXT = """
ccodex commands

/help       Show this help message
/models     List models from the API server
/prompt     Show the active system prompt
/config     Show loaded configuration
/raw        Show the last JSON request payload
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
    # interactive: None or dict with interactive instructions
    interactive: dict | None = None


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

    if command == "/models":
        try:
            models = client.list_models()
        except Exception as exc:
            return CommandResult(
                handled=True,
                output=f"Could not fetch models: {exc}",
            )

        if not models:
            return CommandResult(
                handled=True,
                output="No models returned by the API server.",
            )

        lines = ["Available models"]

        for model in models:
            model_id = model.get("id", "<unknown>")
            owned_by = model.get("owned_by")
            max_len = model.get("max_model_len")

            details = []

            if owned_by:
                details.append(f"owner: {owned_by}")

            if max_len:
                details.append(f"context: {max_len}")

            suffix = f" ({', '.join(details)})" if details else ""
            lines.append(f"- {model_id}{suffix}")

        return CommandResult(
            handled=True,
            output="\n".join(lines),
        )

    if command == "/prompt":
        prompt = build_system_prompt(config)

        output = f"""
        Active system prompt

        Path: {config.system_prompt_path}

        {prompt}
        """.strip()

        return CommandResult(
            handled=True,
            output=output,
        )
        
    if command == "/config":
        output = "\n".join(
            [
                "Loaded configuration",
                "",
                f"Config file:        {config.config_path}",
                f"Config file loaded: {'yes' if config.config_loaded else 'no'}",
                f"Base URL:           {config.base_url}",
                f"Model:              {config.model}",
                f"API key configured: {'yes' if config.api_key.strip() else 'no'}",
                f"Temperature:        {config.temperature}",
                f"Max tokens:         {config.max_tokens}",
                f"Timeout:            {config.timeout}",
                f"History limit:      {config.history_limit}",
                f"System prompt path: {config.system_prompt_path}",
            ]
        )

        return CommandResult(
            handled=True,
            output=output,
        )
            

    if command == "/raw":
        if client.stats.last_payload is None:
            return CommandResult(
                handled=True,
                output="No raw request payload yet. Send a message to the model first.",
            )

        output = json.dumps(
            client.stats.last_payload,
            indent=2,
            ensure_ascii=False,
        )

        return CommandResult(
            handled=True,
            output=output,
        )

    if command == "/clear":
        history.clear()
        return CommandResult(handled=True, output="Conversation history cleared.")

    if command == "/history":
        return CommandResult(handled=True, output=history.format_history())

    # Read file contents (safe, repo-relative)
    if command == "/read":
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return CommandResult(handled=True, output="Usage: /read <path>")

        raw_path = parts[1].strip()
        path = Path(raw_path).expanduser()

        # Deny absolute paths for safety in this initial implementation
        if path.is_absolute():
            return CommandResult(handled=True, output="/read only accepts repository-relative paths.")

        # Prevent path traversal outside cwd
        if ".." in path.parts:
            return CommandResult(handled=True, output="Path must not contain '..' components.")

        full = Path.cwd() / path

        if not full.exists():
            return CommandResult(handled=True, output=f"File not found: {raw_path}")

        try:
            text_content = full.read_text(encoding="utf-8")
        except Exception as exc:
            return CommandResult(handled=True, output=f"Could not read file: {exc}")

        # Limit output length
        if len(text_content) > 20000:
            snippet = text_content[:20000]
            snippet += "\n... (truncated)"
        else:
            snippet = text_content

        output = f"Reading: {raw_path}\n\n{snippet}"
        return CommandResult(handled=True, output=output)

    # Interactive write: collect multi-line content then present diff and ask to apply
    if command == "/write":
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return CommandResult(handled=True, output="Usage: /write <path>\nAfter running this command you'll be prompted to paste the new file content and finish with a single line containing only .END")

        raw_path = parts[1].strip()
        path = Path(raw_path)

        # safety checks
        if path.is_absolute() or ".." in path.parts:
            return CommandResult(handled=True, output="/write only accepts safe relative paths (no absolute or .. components).")

        # Ask the chat loop to collect multi-line input
        return CommandResult(
            handled=True,
            output=(f"Please paste the new contents for {raw_path}.\nEnd with a line containing only .END"),
            interactive={"type": "collect_multiline", "path": str(path)},
        )

    if command == "/stats":
        latency = client.stats.last_latency_seconds
        latency_text = "n/a" if latency is None else f"{latency:.2f}s"
        error_text = client.stats.last_error or "none"

        output = "\n".join(
            [
                "Runtime stats:",
                "",
                f"Base URL:      {config.base_url}",
                f"Model:         {config.model}",
                f"Temperature:   {config.temperature}",
                f"Max tokens:    {config.max_tokens}",
                f"History turns: {history.turns}",
                f"Requests:      {client.stats.requests}",
                f"Last latency:  {latency_text}",
                f"Last chars:    {client.stats.last_chars}",
                f"Last error:    {error_text}",
            ]
        ).strip()
        return CommandResult(handled=True, output=output)

    # Project scan for awareness
    if command == "/scan":
        parts = text.split(maxsplit=1)
        target = parts[1].strip() if len(parts) > 1 else "."

        try:
            from engine.project import scan_project

            results = scan_project(target, max_files=200)
        except Exception as exc:
            return CommandResult(handled=True, output=f"Scan failed: {exc}")

        if not results:
            return CommandResult(handled=True, output=f"No files found under {target}.")

        lines = [f"Scan results for {target} (showing {len(results)} files):", ""]
        for entry in results[:50]:
            lines.append(f"- {entry['path']} ({entry['language']}, {entry['size']} bytes)")

        return CommandResult(handled=True, output="\n".join(lines))

    # Export conversation history to a file (markdown)
    if command == "/export":
        parts = text.split(maxsplit=1)
        raw_path = parts[1].strip() if len(parts) > 1 else None

        from datetime import datetime

        if raw_path:
            path = Path(raw_path)
        else:
            t = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            path = Path(f"ccodex_export_{t}.md")

        # safety checks
        if path.is_absolute() or ".." in path.parts:
            return CommandResult(handled=True, output="/export only accepts repository-relative paths.")

        try:
            content = history.format_history()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except Exception as exc:
            return CommandResult(handled=True, output=f"Export failed: {exc}")

        return CommandResult(handled=True, output=f"Exported history to {path}")

    return CommandResult(
        handled=True,
        output=f"Unknown command: {command}\nType /help for available commands.",
    )
