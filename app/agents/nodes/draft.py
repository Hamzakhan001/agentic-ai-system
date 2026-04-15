from __future__ import annotations

import json

from app.agents.prompts import (
    NEXT_STEPS_DRAFT_SYSTEM,
    RISK_REVIEW_DRAFT_SYSTEM,
    SUMMARY_DRAFT_SYSTEM,
    TIMELINE_DRAFT_SYSTEM,

)

from app.agents.state import AgentState


def _build_payload(state: AgentState) -> str:
    docs = state.get("retrieved_documents", [])
    evidence = [
        {
            "document_id": doc.id,
            "title": doc.title,
            "text": doc.text[:2500]
        }
        for doc in docs
    ]

    return json.dumps(
        {
            "question": state["question"],
            "evidence": state["task_type"],
            "facts": state.get("extracted_facts", []),
            "documents": evidence,
        },
        ensure_ascii = False
    )

async def draft_summary(state: AgentState, llm) -> AgentState:
    answer = await llm.complete(
        system = SUMMARY_DRAFT_SYSTEM,
        user = _build_payload(state)
    )

    return { **state, "draft_answer": answer}


async def draft_timeline(state: AgentState, llm) -> AgentState:
    answer = await llm.complete(
        system = TIMELINE_DRAFT_SYSTEM,
        user = _build_payload(state)
    )

    return { **state, "draft_answer": answer}


async def draft_risk_review(state: AgentState, llm) -> AgentState:
    answer = await llm.complete(
        system = RISK_REVIEW_DRAFT_SYSTEM,
        user = _build_payload(state)
    )

    return { **state, "draft_answer": answer}

async def draft_next_steps(state: AgentState, llm) -> AgentState:
    answer = await llm.complete(
        system = NEXT_STEPS_DRAFT_SYSTEM,
        user = _build_payload(state)
    )

    return { **state, "draft_answer": answer}