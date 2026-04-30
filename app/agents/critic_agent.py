from __future__ import annotations
import json
from app.agents.base import BaseAgent
from app.agents.prompts import get_critique_system
from app.agents.state import AgentState
from opentelemetry import trace


class CriticAgent(BaseAgent):
    name = "critic_agent"

    def __init__(self, llm) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict:
        if state["task_type"] == "evidence_extraction":
            return {
                "critique": {
                    "verdict": "pass",
                    "issues": [],
                    "missing_information": []
                }
            }

        docs = state.get("retrieved_documents", [])

        evidence = [
            {
                "document_id": doc.id,
                "title": doc.title,
                "text": doc.text[:2500],
            }
            for doc in docs
        ]

        prompt = get_critique_system()
        span = trace.get_current_span()
        if span is not None:
            span.set_attribute("prompt.name", prompt["name"])
            span.set_attribute("prompt.tag", prompt["tag"])
            span.set_attribute("prompt.version_id", prompt["version_id"] or "fallback")
            span.set_attribute("prompt.source", prompt["source"])

        
        critique_result = await self.llm.json_response(
            system = prompt["content"],
            user = json.dumps(
                {
                    "question": state["question"],
                    "task_type": state["task_type"],
                    "draft_answer": state.get("draft_answer", ""),
                    "documents": evidence,
                    "facts": state.get("extracted_facts",[]),
                    "external_context": state.get("external_context", []),
                },
                ensure_ascii=False
            )
        )

        return {
            "critique": critique_result
        }
