from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

from app.core.models import InputDocument


class AgentState(TypedDict, total = False):
    question: str
    task_type: Literal["summary", "timeline", "risk_review", "next_steps", "evidence_extraction"]
    documents: list[InputDocument]
    document_ids: list[str]
    top_k: int
    retrieved_documents: list[InputDocument]
    extracted_facts: list[dict[str, Any]]
    draft_answer: str
    critique: dict[str, Any]
    final_answer: str
    retry_count: int
    sources: list[dict[str, str]]
    error: Optional[str]



