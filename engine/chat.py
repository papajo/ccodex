from __future__ import annotations
from engine.prompting import build_system_prompt
from engine.client import OpenAICompatibleClient
from engine.commands import handle_command
from engine.config import Config
from engine.history import ChatHistory
from pathlib import Path
import os


def run_chat(config: Config) -> None:
    system_prompt = build_system_prompt(config)

    # persistent history path can be configured via `CCODEX_HISTORY_PATH`
    history_path = Path(os.getenv("CCODEX_HISTORY_PATH", ".ccodex_history.json"))
    history = ChatHistory.load(history_path, limit=config.history_limit)
    client = OpenAICompatibleClient(config=config)

    print("ccodex v0.2")
    print(f"model: {config.model}")
    print(f"server: {config.base_url}")
    print("type /help for commands, /exit to quit")
    print()

    while True:
        try:
            user_input = input("ccodex> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break

        if not user_input:
            continue

        command = handle_command(
            user_input,
            history=history,
            config=config,
            client=client,
        )

        if command.handled:
            if command.output:
                print(command.output)

            # Interactive collection (multi-line) support
            if getattr(command, "interactive", None):
                intr = command.interactive
                if intr.get("type") == "collect_multiline":
                    path = intr.get("path")
                    lines: list[str] = []
                    print("(paste content, end with .END on its own line)")
                    while True:
                        try:
                            line = input()
                        except (EOFError, KeyboardInterrupt):
                            print("\nAborted.")
                            lines = []
                            break

                        if line.strip() == ".END":
                            break

                        lines.append(line)

                    if not lines:
                        # nothing collected / aborted
                        continue

                    new_text = "\n".join(lines) + "\n"
                    from pathlib import Path
                    import difflib
                    target = Path(Path.cwd()) / Path(path)
                    old_text = ""
                    if target.exists():
                        try:
                            old_text = target.read_text(encoding="utf-8")
                        except Exception:
                            old_text = ""

                    old_lines = old_text.splitlines(keepends=True)
                    new_lines = new_text.splitlines(keepends=True)

                    diff = "".join(
                        difflib.unified_diff(old_lines, new_lines, fromfile=str(target), tofile=str(target) + " (new)")
                    )

                    if not diff:
                        print("No changes detected.")
                        continue

                    print("--- Diff preview ---")
                    print(diff)
                    ans = input("Apply changes? (y/N): ").strip().lower()
                    if ans in {"y", "yes"}:
                        # create parent dirs
                        target.parent.mkdir(parents=True, exist_ok=True)
                        # backup
                        if target.exists():
                            try:
                                bak = target.with_suffix(target.suffix + ".bak")
                                bak.write_text(old_text, encoding="utf-8")
                            except Exception:
                                pass

                        try:
                            target.write_text(new_text, encoding="utf-8")
                            print(f"Wrote {target}")
                        except Exception as exc:
                            print(f"Failed to write file: {exc}")
                    else:
                        print("Aborted — no changes applied.")

            if command.should_exit:
                break
            continue

        history.add_user(user_input)
        messages = history.to_messages(system_prompt)

        print("assistant> ", end="", flush=True)

        chunks: list[str] = []

        try:
            for chunk in client.stream_chat(messages):
                print(chunk, end="", flush=True)
                chunks.append(chunk)

            print()

        except Exception as exc:
            history.remove_last()
            print()
            print(f"[error] {exc}")
            print("Check that your OpenAI-compatible local server is running.")
            continue

        assistant_text = "".join(chunks).strip()

        if assistant_text:
            history.add_assistant(assistant_text)

    # Save history on exit (best-effort)
    try:
        history.save(history_path)
    except Exception:
        pass
