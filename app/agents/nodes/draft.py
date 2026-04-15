from __future__ import annotations

import json

from app.agents.prompts import DRAFT_SYSTEM
from app.agents.state import AgentState


async def draft(state: AgentState, llm) -> AgentState:
    docs = state.get("retrieved_documents", [])
    evidence = [
        {"document_id": doc.id, "title": doc.title, "text": doc.text[:2500]}
        for doc in docs
    ]
    answer = await llm.complete(
        system=DRAFT_SYSTEM,
        user=json.dumps(
            {
                "question": state["question"],
                "task_type": state["task_type"],
                "facts": state.get("extracted_facts", []),
                "documents": evidence,
            },
            ensure_ascii=False,
        ),
    )
    return {**state, "draft_answer": answer}
