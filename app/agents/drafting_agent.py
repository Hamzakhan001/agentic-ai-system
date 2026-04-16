from __future__ import annotations
import json

from app.agents.base import BaseAgent
from app.agents.prompts import (
    NEXT_STEPS_DRAFT_SYSTEM,
    RISK_REVIEW_DRAFT_SYSTEM,
    SUMMARY_DRAFT_SYSTEM,
    TIMELINE_DRAFT_SYSTEM
)

from app.agents.state import AgentState

class DraftingAgent(BaseAgent):
    name = "drafting_agent"

    def __init__(self, llm) -> None:
        self.llm = llm

    def _select_prompt(self, task_type: str) -> str:
        if task_type == "summary":
            return SUMMARY_DRAFT_SYSTEM
        if task_type == "timeline":
            return TIMELINE_DRAFT_SYSTEM
        if task_type == "risk_review":
            return RISK_REVIEW_DRAFT_SYSTEM
        if task_type == "next_steps":
            return NEXT_STEPS_DRAFT_SYSTEM
        
        return SUMMARY_DRAFT_SYSTEM


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

        answer = await self.llm.complete(
            system = self._select_prompt(state["task_type"]),
            user = json.dumps(
                {
                    "question": state["question"],
                    "task_type": state["task_type"],
                    "facts": state.get("extracted_facts",[]),
                    "documents": evidence
                },
                ensure_ascii=False
            )
        )

        return {
            "draft_answer": answer
        }
