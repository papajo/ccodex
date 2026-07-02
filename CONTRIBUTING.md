# CONTRIBUTING

Thank you for contributing to ccodex.

Developer quick start

- Create a virtualenv and install test deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install pytest
```

- Run tests:

```bash
pytest -q
```

Feature notes

- Commands live in `engine/commands.py`.
- Interactive chat loop is in `engine/chat.py`.
- Project scanning helper: `engine/project.py`.
- Conversation history persistence: `engine/history.py` (`save`/`load`).

Safety

- The `/write` command previews a unified diff and requires confirmation.
- The CLI performs basic secret detection and will abort unless `FORCE` is supplied.

License: MIT
