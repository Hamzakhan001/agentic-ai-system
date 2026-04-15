from __future__ import annotations

import json

from app.agents.prompts import EXTRACTION_SYSTEM
from app.agents.state import AgentState

async def extract(state: AgentState, llm) -> AgentState:
    docs = state.get("retrieved_documents", [])

    evidence = [
        {
            "document_id": doc.id,
            "title": doc.title,
            "text": doc.text[:4000],
        }
        for doc in docs
    ]
    payload = await llm.json_response(
        system=EXTRACTION_SYSTEM,
        user=json.dumps(
            {"question": state["question"], "task_type": state["task_type"], "documents": evidence},
            ensure_ascii=False,
        ),
    )
    return {**state, "extracted_facts": payload.get("facts", [])}