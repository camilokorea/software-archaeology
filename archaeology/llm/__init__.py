"""Model providers. Each one takes a system prompt, a user prompt and a JSON schema, and returns parsed JSON."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.calls += other.calls

    def cost(self, prices: dict) -> float:
        return round(self.input_tokens / 1e6 * prices["input"] + self.output_tokens / 1e6 * prices["output"], 4)


class ProviderError(RuntimeError):
    """The model call failed in a way the pipeline reports and moves past (the spec is skipped, not the run)."""


class FatalProviderError(ProviderError):
    """Every further call would fail the same way (bad key, no credit): stop asking, keep the verified findings."""


@dataclass
class Provider:
    name: str = "none"
    model: str | None = None
    info: dict = field(default_factory=dict)

    def complete(self, system: str, user: str, schema: dict, label: str) -> tuple[dict, Usage]:
        raise NotImplementedError


def make(cfg: dict, prompts_dir=None) -> Provider | None:
    ai = cfg["ai"]
    if ai["provider"] == "anthropic":
        from archaeology.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=ai["model"] or "claude-opus-5-5", effort=ai["effort"])
    if ai["provider"] == "ollama":
        from archaeology.llm.ollama_provider import OllamaProvider

        return OllamaProvider(model=ai["model"] or "qwen2.5-coder:14b", url=ai["ollama_url"], temperature=ai["temperature"])
    return None
