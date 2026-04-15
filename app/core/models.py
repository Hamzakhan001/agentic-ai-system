from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


TaskType = Literal["summary", "timeline", "risk_review", "next_steps", "evidence_extraction"]


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