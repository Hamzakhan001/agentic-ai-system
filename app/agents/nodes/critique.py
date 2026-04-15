from __future__ import annotations

import json

from app.agents.prompts import CRITIQUE_SYSTEM
from app.agents.state import AgentState


async def critique(state: AgentState, llm) -> AgentState:
    docs = state.get("retrieved_documents", [])
    evidence = [
        {"document_id": doc.id, "title": doc.title, "text": doc.text[:2500]}
        for doc in docs
    ]
    critique_result = await llm.json_response(
        system=CRITIQUE_SYSTEM,
        user = json.dumps(
            {
                "question": state["question"],
                "task_type": state["task_type"],
                "draft_answer": state.get("draft_answer", ""),
                "documents": evidence,
                "facts": state.get("extracted_facts", []),
            },
            ensure_ascii=False,
        ),
    )
    return {**state, "critique": critique_result}
