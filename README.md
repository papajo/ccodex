# ccodex

A transparent, hackable, local-first CLI coding assistant.

`ccodex` is a small command-line coding assistant designed to work with local or OpenAI-compatible model servers such as oMLX, Ollama-compatible gateways, vLLM, LM Studio, or remote OpenAI-compatible APIs.

The goal is not to clone Codex, Claude Code, Cursor, or OpenCode feature-for-feature. The goal is to build a coding assistant that is:

- small enough to understand
- easy to modify
- model-agnostic
- transparent about prompts and context
- friendly to local models
- safe by default

Current version: **v0.2**

---

## Why ccodex?

Most coding agents hide too much:

- hidden prompts
- unclear request payloads
- unclear context usage
- unclear tool execution
- unclear model behavior

`ccodex` is built around the opposite idea.

You should be able to inspect what it sends, what it remembers, what model it is using, and eventually what files/tools it is touching.

This project is both a useful CLI assistant and a learning project for understanding how LLM coding agents work under the hood.

---

## Current features

v0.2 includes:

- CLI chat loop
- OpenAI-compatible `/v1/chat/completions` support
- streaming responses
- conversation history
- external system prompt
- local commands
- basic runtime stats
- environment-based configuration
- installable `ccodex` command

---

## Project structure

```text
ccodex/
├── engine/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── chat.py
│   ├── client.py
│   ├── commands.py
│   ├── config.py
│   ├── history.py
│   └── prompts/
│       └── system.md
├── tests/
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Requirements

- Python 3.10+
- A running OpenAI-compatible API server
- A model available through that server

Tested with:

- oMLX
- `Ornith-1.0-9B-4bit`
- local API server at `http://localhost:8001/v1`

---

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install -e .
```

Confirm the command is available:

```bash
which ccodex
```

You should see something like:

```text
/path/to/ccodex/.venv/bin/ccodex
```

---

## Configuration

`ccodex` currently uses environment variables.

Minimum configuration:

```bash
export CCODEX_BASE_URL="http://localhost:8001/v1"
export CCODEX_MODEL="Ornith-1.0-9B-4bit"
export CCODEX_API_KEY="your-local-server-api-key"
```

Optional configuration:

```bash
export CCODEX_TEMPERATURE="0.2"
export CCODEX_MAX_TOKENS="2048"
export CCODEX_TIMEOUT="120"
export CCODEX_HISTORY_LIMIT="20"
```

Do not commit API keys.

Use environment variables or a local ignored `.env` file.

---

## Running ccodex

Start the CLI:

```bash
ccodex
```

Or run directly:

```bash
python main.py
```

Or:

```bash
python -m engine
```

Expected startup:

```text
ccodex v0.2
model: Ornith-1.0-9B-4bit
server: http://localhost:8001/v1
type /help for commands, /exit to quit

ccodex>
```

---

## Commands

Inside the CLI:

```text
/help       Show available commands
/clear      Clear conversation history
/history    Show current conversation history
/stats      Show runtime stats
/exit       Exit ccodex
/quit       Exit ccodex
```

Anything else is sent to the model.

Example:

```text
ccodex> hello, reply with one short sentence
assistant> Hello! How can I help you today?
```

---

## System prompt

The active system prompt lives at:

```text
engine/prompts/system.md
```

You can edit it without changing Python code.

Current default:

```text
You are ccodex, a transparent, local-first coding assistant.

Principles:
- Be concise but complete.
- Prefer direct, working code over vague advice.
- Explain tradeoffs when they matter.
- Do not pretend to edit files unless tools are available.
- Ask before destructive changes.
- Make hidden assumptions visible.
```

---

## Local model files

Do not store model weights inside this repository.

Recommended locations:

```text
~/models/
~/ai-models/
~/mlx-models/
```

Avoid committing:

```text
*.safetensors
*.gguf
*.bin
*.pt
*.pth
Ornith*/
huggingface:*/
models/
```

The repo should contain code, not model weights.

---

## Development workflow

Run syntax checks:

```bash
python -m py_compile engine/*.py
```

Check Git state:

```bash
git status --short
```

Install after changing packaging:

```bash
python -m pip install -e .
```

Run the CLI:

```bash
ccodex
```

---

## Version tags

Known working checkpoints are tagged.

Current stable tag:

```bash
git tag
```

v0.2 means:

```text
Working CLI foundation with local commands, streaming chat, history, and oMLX-compatible API support.
```

To inspect that version:

```bash
git checkout v0.2
```

Return to normal development:

```bash
git checkout main
```

---

## Roadmap

### v0.3 — Transparency and configuration

Planned:

- `/models` — list available models from the API server
- `/prompt` — print the active system prompt
- `/config` — show loaded configuration
- `/raw` — show the exact JSON payload before sending
- `config.toml` support

### v0.4 — File awareness

Planned:

- read a specific file
- explain a file
- summarize a file
- include file content in model context safely

Example future usage:

```text
ccodex> explain engine/client.py
```

### v0.5 — Project awareness

Planned:

- inspect repository structure
- select relevant files
- summarize project layout
- avoid sending the entire repo blindly

### v0.6 — Diff-based edits

Planned:

- generate patches
- show diffs before applying
- ask for confirmation
- avoid silent file mutation

### v0.7 — Explicit tools

Planned safe tools:

- read file
- write file
- search files
- git status
- git diff
- run tests
- inspect project metadata

Tool use should be visible and confirmable.

---

## Design principles

### 1. No hidden magic

Prompts, context, payloads, and tool behavior should be inspectable.

### 2. Local-first

The assistant should work well with local models and local API servers.

### 3. Small core

Prefer simple Python modules over a giant framework.

### 4. Safe by default

Reading is safe. Writing should be explicit. Destructive actions should require confirmation.

### 5. Model-agnostic

The client should work with any server that behaves like an OpenAI-compatible chat completions API.

---

## Status

`ccodex` is early but functional.

Current state:

```text
v0.2 working
```

The next major milestone is v0.3: inspection commands and config support.