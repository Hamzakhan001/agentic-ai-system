from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


TaskType = Literal["summary", "timeline", "risk_review", "next_steps", "evidence_extraction"]

ReviewStatus = Literal[
    "pending",
    "running",
    "completed",
    "approved",
    "revision_requested",
    "failed"
]




class InputDocument(BaseModel):
    id: str
    title: str
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestTextRequest(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    title: str
    chunks: int 

class ReviewRequest(BaseModel):
    question: str = Field(min_length=1)
    task_type: Optional[TaskType] = None
    documents: list[InputDocument] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = 4

    @model_validator(mode="after")
    def validate_sources(self) -> "ReviewRequest":
        if not self.documents and not self.document_ids:
            raise ValueError("Provide either documents or document_ids")
        return self


class ExtractedFact(BaseModel):
    type: str
    value: str
    source_document_id: str
    confidence: float


class CritiqueResult(BaseModel):
    verdict: Literal["pass", "revise"]
    issues: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class SourceSnippet(BaseModel):
    document_id: str
    title: str
    snippet: str

class ReviewResponse(BaseModel):
    task_type: TaskType
    extracted_facts: list[ExtractedFact]
    draft_answer: str
    critique: CritiqueResult
    final_answer: str
    sources: list[SourceSnippet]


class ReviewSummary(BaseModel):
    id: str
    parent_run_id: Optional[str] = None
    question: str
    task_type: Optional[str] = None
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class ReviewRunDetail(BaseModel):
    id: str
    parent_run_id: Optional[str] = None
    question: str
    task_type: Optional[str] = None
    status: ReviewStatus
    top_k: int
    review_note: Optional[str] = None
    error_message: Optional[str] =None
    extracted_facts: list[dict[str, Any]] = Field(default_factory=list)
    draft_answer: str = ""
    critique: dict[str, Any] = Field(default_factor = dict)
    final_answer: str = ""
    sources: list[dict[str, Any]] = Field(default_factory=list)
    external_context: list[dict[str, Any]] = Field(default_factory=list)

class ApproveRunRequest(BaseModel):
    reviewer_name: str = "reviewer"
    reviewer_note: Optional[str] = None

class ReviseRunRequest(BaseModel):
    instructions: str = Field(min_length=3)
    reviewer_name: str = "reviewer"
    rerun: bool = True
