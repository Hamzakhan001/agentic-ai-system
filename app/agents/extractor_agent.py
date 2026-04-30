from __future__ import annotations
import json
from app.agents.base import BaseAgent
from app.agents.prompts import get_extraction_system
from app.agents.state import AgentState
from opentelemetry import trace



class ExtractorAgent(BaseAgent):
    name = "extractor_agent"

    def __init__(self, llm) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict:
        docs = state.get("retrieved_documents", [])

        evidence = [
            {
                "document_id": doc.id,
                "title": doc.title,
                "text": doc.text[:4000],
            }
            for doc in docs
        ]
        prompt = get_extraction_system()
        span = trace.get_current_span()
        if span is not None:
            span.set_attribute("prompt.name", prompt["name"])
            span.set_attribute("prompt.tag", prompt["tag"])
            span.set_attribute("prompt.version_id", prompt["version_id"] or "fallback")
            span.set_attribute("prompt.source", prompt["source"])

        payload = await self.llm.json_response(
            system=prompt["content"],
            user = json.dumps(
                {
                    "question": state["question"],
                    "task_type": state["task_type"],
                    "documents": evidence,
                    "external_context": state.get("external_context", [])
                },
                ensure_ascii = False
            )
        )

        return {
            "extracted_facts": payload.get("facts", [])
        }