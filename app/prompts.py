from __future__ import annotations
from functools import lru_cache
from config.settings import get_settings


RAG_PROMPT_FALLBACK = (
    "You are a reterival-augmented assistant."
    "Answer the user's questions using only the provided context"
    "If the context contains enough information, answer clearly and directly"
    "If the context does not contain the answer, say that the answer is not available in the provided documents"
    "Do not fabricate facts or rely on outside knowledge \n\n"
    "Context: \n{context}"
)


@lru_cache(maxsize=64)
def get_prompt_text(prompt_identifier:str, fallback:str, tag:str = "production") -> str:
    try:
        from phoenix.client import Client

        client = Client()
        prompt = client.prompts.get(
            prompt_identifier = prompt_identifier,
            tag=tag
        )
        messages = prompt.version.template.messages
        system_message = next(m for m in messages if m["role"] == "system")
        return system_message["content"]
    except Exception:
        return fallback
