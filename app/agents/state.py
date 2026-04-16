from __future__ import annotations
from typing import Literal, Any, Optional,TypedDict
from app.core.models import InputDocument

TaskType = Literal[
    "summary",
    "timeline",
    "risk_review",
    "next_steps",
    "evidence_extraction"
]

class AgentState(TypedDict, total=False):
    review_run_id: str

    question: str
    task_type: TaskType
    routing_reason: str

    documents: list[InputDocument]
    document_ids: list[str]
    top_k: int
    
    retrieved_documents: list[InputDocument]
    source_ids: list[str]
    external_context: list[dict[str, Any]]

    extracted_facs: list[dict[str, Any]]
    draft_answer: str
    critique: dict[str, Any]
    final_answer: str
    sources: list[dict[str str]]

    retry_count: int
    error: Optional[str]