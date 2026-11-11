"""Claude through the official Anthropic SDK, with structured output so the model can only answer in the schema.
Refusals fall back server-side to the model Anthropic recommends for that case (fallbacks="default")."""

from __future__ import annotations

import json

from archaeology.llm import FatalProviderError, Provider, ProviderError, Usage


class AnthropicProvider(Provider):
    def __init__(self, model: str, effort: str = "medium"):
        super().__init__(name="anthropic", model=model, info={"effort": effort, "fallbacks": "default"})
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover - depends on the environment
            raise ProviderError("The anthropic package is not installed: pip install 'software-archaeology[anthropic]'") from e
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=4)  # retries 408/409/429/5xx and connection errors with backoff
        self.effort = effort

    def complete(self, system: str, user: str, schema: dict, label: str) -> tuple[dict, Usage]:
        a = self._anthropic
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
            )
        except a.RateLimitError as e:
            raise ProviderError(f"{label}: rate limited after retries ({e})") from e
        except (a.AuthenticationError, a.PermissionDeniedError) as e:
            raise FatalProviderError("Anthropic rejected the API key or its permissions (check ANTHROPIC_API_KEY)") from e
        except a.BadRequestError as e:
            if "credit balance" in str(e).lower():
                raise FatalProviderError("The Anthropic account has no credit left (Plans & Billing)") from e
            raise ProviderError(f"{label}: request rejected ({e})") from e
        except a.APIStatusError as e:
            raise ProviderError(f"{label}: API error {e.status_code}") from e
        except a.APIConnectionError as e:
            raise ProviderError(f"{label}: could not reach the API ({e})") from e
        usage = Usage(response.usage.input_tokens, response.usage.output_tokens, 1)
        if response.stop_reason == "refusal":
            raise ProviderError(f"{label}: the model declined this request")
        if response.stop_reason == "max_tokens":
            raise ProviderError(f"{label}: the answer was cut off (max_tokens)")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise ProviderError(f"{label}: empty answer (stop_reason={response.stop_reason})")
        try:
            return json.loads(text), usage
        except ValueError as e:
            raise ProviderError(f"{label}: answer was not valid JSON") from e
