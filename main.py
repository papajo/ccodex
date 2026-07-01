import typer
import requests
from rich.console import Console

app = typer.Typer()
console = Console()

API_KEY = "padoshiomlx"
MODEL = "Ornith-1.0-9B-4bit"

SYSTEM_PROMPT = """You are a precise coding assistant.
You write correct, minimal, production-grade code.
You do not hallucinate APIs.
If unsure, say so.
"""

def chat(user):
    r = requests.post(
        "http://localhost:8001/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user}
            ]
        }
    )

    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

@app.command()
def run():
    console.print("ccodex ready (type 'exit' to quit)\n")

    while True:
        user = input(">>> ")
        if user in ["exit", "quit"]:
            break

        try:
            out = chat(user)
            console.print("\n" + out + "\n")
        except Exception as e:
            console.print(f"[red]error:[/red] {e}")

if __name__ == "__main__":
    app()