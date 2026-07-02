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
                    dry_run = intr.get("dry_run", False)
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
                        # basic secret scanning (v0.7 safety)
                        import re

                        secret_patterns = [
                            r"API[_-]?KEY\s*=",  # API_KEY= or API-KEY =
                            r"SECRET[_-]?KEY",
                            r"AKIA[0-9A-Z]{16}",
                            r"[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}",
                            r"-----BEGIN PRIVATE KEY-----",
                        ]

                        # allow project override from .ccodex_secret_patterns.json
                        try:
                            cfg_file = Path.cwd() / ".ccodex_secret_patterns.json"
                            if cfg_file.exists():
                                import json as _json
                                with cfg_file.open("r", encoding="utf-8") as fh:
                                    extra = _json.load(fh)
                                if isinstance(extra, list):
                                    secret_patterns = extra + secret_patterns
                        except Exception:
                            pass

                        found = []
                        for pat in secret_patterns:
                            if re.search(pat, new_text):
                                found.append(pat)

                        if found:
                            print("Warning: potential secrets detected in the provided content.")
                            print("Matches:")
                            for f in found:
                                print(f"- {f}")
                            confirm = input("Type FORCE to proceed anyway, or anything else to abort: ").strip()
                            if confirm != "FORCE":
                                print("Aborted due to secret detection — no changes applied.")
                                continue

                        # create parent dirs
                        target.parent.mkdir(parents=True, exist_ok=True)

                        if dry_run:
                            print("Dry-run: not writing file. Dry diff saved to .ccodex_dryrun.diff")
                            try:
                                with open(".ccodex_dryrun.diff", "w", encoding="utf-8") as fh:
                                    fh.write(diff)
                            except Exception:
                                pass
                            continue

                        # backup
                        if target.exists():
                            try:
                                bak = target.with_suffix(target.suffix + ".bak")
                                bak.write_text(old_text, encoding="utf-8")
                            except Exception:
                                pass

                        try:
                            # If file changed on disk since preview, attempt three-way merge via git
                            current_text = ""
                            if target.exists():
                                try:
                                    current_text = target.read_text(encoding="utf-8")
                                except Exception:
                                    current_text = old_text

                            if current_text != old_text and target.exists():
                                # write new_text to a temp file and run git merge-file
                                import tempfile, subprocess

                                with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as newf:
                                    newf.write(new_text)
                                    new_path = newf.name

                                with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as basef:
                                    basef.write(old_text)
                                    base_path = basef.name

                                # current file on disk is the local
                                local_path = str(target)

                                try:
                                    rc = subprocess.call(["git", "merge-file", local_path, base_path, new_path])
                                    if rc == 0:
                                        print(f"Three-way merge applied to {target}")
                                    else:
                                        print(f"Merge had conflicts (exit {rc}). Created .rej files if any.")
                                except Exception:
                                    # fallback to overwrite
                                    target.write_text(new_text, encoding="utf-8")
                                    print(f"Wrote {target} (fallback)")
                                finally:
                                    try:
                                        Path(new_path).unlink()
                                    except Exception:
                                        pass
                                    try:
                                        Path(base_path).unlink()
                                    except Exception:
                                        pass
                            else:
                                target.write_text(new_text, encoding="utf-8")
                                print(f"Wrote {target}")
                        except Exception as exc:
                            print(f"Failed to write file: {exc}")
                            continue

                        # Offer to create a git commit for the change (if in a git repo)
                        try:
                            import subprocess

                            git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
                            if git_root.returncode == 0:
                                do_commit = input("Create git commit for this change? (y/N): ").strip().lower()
                                if do_commit in {"y", "yes"}:
                                    try:
                                        subprocess.check_call(["git", "add", str(target)])
                                        msg = f"ccodex: update {target}"
                                        subprocess.check_call(["git", "commit", "-m", msg])
                                        print("Committed change to git.")
                                    except Exception as exc:
                                        print(f"Git commit failed: {exc}")
                        except Exception:
                            pass
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
