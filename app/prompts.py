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

        messages = prompt._template["messages"]
        system_message = next(m for m in messages if m["role"] == "system")
        system_text = "\n".join(
            block["text"]
            for block in system_message["content"]
            if block.get("type") == "text"
        )

        return {
            "name": prompt_identifier,
            "tag": tag,
            "version_id": prompt.id,
            "content": system_text,
            "source": "phoenix",
        }
    except Exception as exc:
        print(f"PHOENIX PROMPT FETCH FAILED: {prompt_identifier}: {exc}")
        return {
            "name": prompt_identifier,
            "tag": tag,
            "version_id": None,
            "content": fallback,
            "source": "fallback",
        }
