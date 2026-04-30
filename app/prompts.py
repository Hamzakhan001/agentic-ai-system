from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=64)
def get_prompt(
    prompt_identifier: str,
    fallback: str,
    tag: str = "production",
) -> dict[str, str | None]:
    try:
        from phoenix.client import Client

        client = Client()
        prompt = client.prompts.get(
            prompt_identifier=prompt_identifier,
            tag=tag,
        )

        messages = prompt.version.template.messages
        system_message = next(m for m in messages if m["role"] == "system")

        return {
            "name": prompt_identifier,
            "tag": tag,
            "version_id": getattr(prompt.version, "id", None),
            "content": system_message["content"],
            "source": "phoenix",
        }
    except Exception:
        return {
            "name": prompt_identifier,
            "tag": tag,
            "version_id": None,
            "content": fallback,
            "source": "fallback",
        }
