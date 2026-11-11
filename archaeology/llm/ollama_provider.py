"""A local model through Ollama, for code that must not leave the machine. Ollama constrains the answer to the
JSON schema with its `format` parameter."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from archaeology.llm import Provider, ProviderError, Usage


class OllamaProvider(Provider):
    def __init__(self, model: str, url: str, temperature: float | None = None):
        super().__init__(name="ollama", model=model, info={"url": url})
        self.url = url.rstrip("/")
        self.temperature = 0 if temperature is None else temperature

    def complete(self, system: str, user: str, schema: dict, label: str) -> tuple[dict, Usage]:
        body = {"model": self.model, "stream": False, "format": schema, "options": {"temperature": self.temperature},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        last: Exception | None = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(f"{self.url}/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=900) as r:
                    data = json.loads(r.read())
                text = data["message"]["content"]
                usage = Usage(data.get("prompt_eval_count", 0), data.get("eval_count", 0), 1)
                return json.loads(text), usage
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
                last = e
                time.sleep(2 ** attempt)
        raise ProviderError(f"{label}: Ollama at {self.url} failed after 3 attempts ({last})")
