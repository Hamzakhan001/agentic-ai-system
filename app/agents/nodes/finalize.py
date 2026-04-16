from __future__ import annotations


import json

from app.agents.prompts import FINALIZE_SYSTEM
from app.agents.state import AgentState


def _format_extracted_facts(state: AgentState) -> str:
    facts = state.get("extracted_facts", [])

    if not facts:
        return "No specific facts extracted."
    
    lines = []
    for fact in facts:
        lines.append(
            f"-{fact['type']}: {fact['value']}"
            f" (source: {fact['source_document_id']}, confidence: {fact['confidence']})"
        )

    return "\n".join(lines)


async def finalize(state: AgentState, llm) -> AgentState:

    docs = state.get("retrieved_documents", [])
    critique = state.get("critique", {})

    sources = [
        {
            "document_id": doc.id,
            "title": doc.title,
            "snippet": doc.text[:300]
        }
        for doc in docs
    ]

    if state["task_type"] == "evidence_extraction":
        return {
            **state,
            "final_answer": _format_extracted_facts(state),
            "sources": sources
        }

    if critique.get("verdict") == "pass":
        return {
            **state,
            "final_answer": state.get("draft_answer", ""),
            "sources": sources
        }

    final_answer = await llm.complete(
        system = FINALIZE_SYSTEM,
        user = json.dumps(
            {
                "question": state["question"],
                "task_type": state["task_type"],
                "draft_answer": state.get("draft_answer", ""),
                "critique": critique,
                "facts": state.get("extracted_facts", []),
                "sources": sources
            },
            ensure_ascii = False
        )
    )

    return {
        **state,
        "final_answer": final_answer,
        "sources": sources
    }