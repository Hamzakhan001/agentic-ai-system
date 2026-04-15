from __future__ import annotations

import json

from app.agents.prompts import FINALIZE_SYSTEM
from app.agents.state import AgentState


async def finalize(state: AgentState, llm) -> AgentState:
    docs = state.get("retrieved_documents", [])
    critique = state.get("critique", {})
    sources = [
        {
            "document_id": doc.id,
            "title": doc.title,
            "snippet": doc.text[:300],
        }
        for doc in docs
    ]

    if critique.get("verdict") == "pass":
        return {**state, "final_answer": state.get("draft_answer", ""), "sources": sources}

    final_answer = await llm.complete(
        system=FINALIZE_SYSTEM,
        user=json.dumps(
            {
                "question": state["question"],
                "task_type": state["task_type"],
                "draft_answer": state.get("draft_answer", ""),
                "critique": critique,
                "facts": state.get("extracted_facts", []),
                "sources": sources,
            },
            ensure_ascii=False,
        ),
    )
    return {**state, "final_answer": final_answer, "sources": sources}
