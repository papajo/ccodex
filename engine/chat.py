from __future__ import annotations
from engine.prompting import build_system_prompt
from engine.client import OpenAICompatibleClient
from engine.commands import handle_command
from engine.config import Config
from engine.history import ChatHistory


def run_chat(config: Config) -> None:
    system_prompt = build_system_prompt(config)

    history = ChatHistory(limit=config.history_limit)
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
