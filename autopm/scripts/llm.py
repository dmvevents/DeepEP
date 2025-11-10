import os
from typing import Optional

# Simple provider shim with graceful model fallbacks
class LLM:
    def __init__(self, provider: str, model: str, temperature: float = 0.2, max_output_tokens: int = 3000):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        if provider == "anthropic":
            try:
                from anthropic import Anthropic
            except Exception as e:
                raise RuntimeError("Anthropic SDK not installed. pip install anthropic") from e
            self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "openai":
            try:
                from openai import OpenAI
            except Exception as e:
                raise RuntimeError("OpenAI SDK not installed. pip install openai") from e
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    # one provider-agnostic call
    def complete(self, system: str, user: str) -> str:
        fallback_models = []
        if self.provider == "anthropic":
            # Prefer configured model first, then safe fallbacks
            fallback_models = [
                self.model,
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
            ]
        else:
            fallback_models = [
                self.model,
                "gpt-4.1-mini",
                "gpt-4o-mini",
            ]

        last_err: Optional[Exception] = None
        for m in fallback_models:
            try:
                return self._try_complete(system, user, m)
            except Exception as e:
                last_err = e
                continue
        # If we exhausted all, raise last error for visibility
        if last_err:
            raise last_err
        raise RuntimeError("No models attempted")

    def _try_complete(self, system: str, user: str, model: str) -> str:
        if self.provider == "anthropic":
            # Anthropic Messages API
            resp = self._client.messages.create(
                model=model,
                max_tokens=self.max_output_tokens,
                temperature=self.temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            # concat text parts
            out = []
            for block in getattr(resp, "content", []) or []:
                text = getattr(block, "text", None)
                if text:
                    out.append(text)
            return "".join(out) if out else (getattr(resp, "content", "") or "")
        else:
            # OpenAI Chat Completions API
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system},{"role":"user","content":user}],
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
            )
            return resp.choices[0].message.content
