from __future__ import annotations
import json
from opentelemetry import trace


from app.agents.base import BaseAgent
from app.agents.prompts import (
    get_next_steps_draft_system,
    get_risk_review_draft_system,
    get_summary_draft_system,
    get_timeline_draft_system,
)

from app.agents.state import AgentState

class DraftingAgent(BaseAgent):
    name = "drafting_agent"

    def __init__(self, llm) -> None:
        self.llm = llm

    def _select_prompt(self, task_type: str) -> dict[str, str | None]:
        if task_type == "summary":
            return get_summary_draft_system()
        if task_type == "timeline":
            return get_timeline_draft_system()
        if task_type == "risk_review":
            return get_risk_review_draft_system()
        if task_type == "next_steps":
            return get_next_steps_draft_system()

        return get_summary_draft_system()




    async def run(self, state: AgentState) -> dict:
        if state["task_type"] == "evidence_extraction":
            return {"draft_answer": ""}
        

        docs = state.get("retrieved_documents", [])

        evidence = [
            {
                "document_id": doc.id,
                "title": doc.title,
                "text": doc.text[:2500],
            }
            for doc in docs
        ]
        prompt = self._select_prompt(state["task_type"])
        span = trace.get_current_span()
        if span is not None:
            span.set_attribute("prompt.name", prompt["name"])
            span.set_attribute("prompt.tag", prompt["tag"])
            span.set_attribute("prompt.version_id", prompt["version_id"] or "fallback")
            span.set_attribute("prompt.source", prompt["source"])


        answer = await self.llm.complete(
            system = prompt["content"],
            user = json.dumps(
                {
                    "question": state["question"],
                    "task_type": state["task_type"],
                    "facts": state.get("extracted_facts",[]),
                    "documents": evidence,
                    "external_context": state.get("external_context", []),
                    "memory_context": state.get("memory_context", []),
                },
                ensure_ascii=False
            )
        )

        return {
            "draft_answer": answer
        }
