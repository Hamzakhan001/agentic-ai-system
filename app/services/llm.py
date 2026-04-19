from __future__ import annotations

import json
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings


class LLMService:
    def __init__(self, *, provider: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.settings = settings
        self.provider = (provider or settings.llm_provider).lower()

        if self.provider == "openai":
            self.model = model or settings.openai_model
            self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        elif self.provider == "ollama":
            self.model = model or settings.ollama_model
            self.client = None
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    @classmethod
    def for_eval(cls) -> "LLMService":
        settings = get_settings()
        return cls(provider=settings.eval_llm_provider, model=settings.eval_model)

    async def complete(self, system: str, user: str, temperature: float = 0.1) -> str:
        if self.provider == "openai":
            return await self._complete_openai(system=system, user=user, temperature=temperature)
        if self.provider == "ollama":
            return await self._complete_ollama(system=system, user=user)
        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def json_response(self, system: str, user: str, temperature: float = 0.0) -> Any:
        if self.provider == "openai":
            raw = await self.complete(system=system, user=user, temperature=temperature)
            return self._parse_json(raw)

        if self.provider == "ollama":
            raw = await self._complete_ollama(system=system, user=user, json_mode=True)
            return self._parse_json(raw)

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def _complete_openai(self, system: str, user: str, temperature: float = 0.1) -> str:
        if self.client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    async def _complete_ollama(self, system: str, user: str, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.settings.ollama_base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data.get("message", {}).get("content", "")

    def _parse_json(self, raw: str) -> Any:
        cleaned = raw.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise ValueError(f"Model did not return valid JSON. Raw response: {raw}")
