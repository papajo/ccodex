from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Iterable

import httpx

from engine.config import Config
from engine.history import Message


@dataclass
class ClientStats:
    requests: int = 0
    last_latency_seconds: float | None = None
    last_chars: int = 0
    last_model: str | None = None
    last_error: str | None = None
    last_payload: dict | None = None


@dataclass
class OpenAICompatibleClient:
    config: Config
    stats: ClientStats = field(default_factory=ClientStats)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    def list_models(self) -> list[dict]:
        url = f"{self.config.base_url}/models"

        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.get(
                url,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

        return data.get("data", [])
            
    def stream_chat(self, messages: list[Message]) -> Iterable[str]:
        url = f"{self.config.base_url}/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }
        
        self.stats.last_payload = payload

        started = time.perf_counter()
        chars = 0

        self.stats.requests += 1
        self.stats.last_model = self.config.model
        self.stats.last_error = None

        try:
            with httpx.Client(timeout=self.config.timeout) as client:
                with client.stream(
                    "POST",
                    url,
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    for line in response.iter_lines():
                        if not line:
                            continue

                        if line.startswith("data:"):
                            line = line.removeprefix("data:").strip()

                        if line == "[DONE]":
                            break

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        choices = data.get("choices") or []
                        if not choices:
                            continue

                        choice = choices[0]
                        delta = choice.get("delta") or {}
                        content = delta.get("content")

                        if content:
                            chars += len(content)
                            yield content

                        if choice.get("finish_reason"):
                            break

        except Exception as exc:
            self.stats.last_error = str(exc)
            raise

        finally:
            self.stats.last_latency_seconds = time.perf_counter() - started
            self.stats.last_chars = chars
