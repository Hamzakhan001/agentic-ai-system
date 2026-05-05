from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from app.core.models import InputDocument, TaskType

class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)


class AgentProvider(BaseModel):
    organization: str

class AgentAuthentication(BaseModel):
    type: str = "none"


class AgentCard(BaseModel):
    name: str
    description: str
    version: str
    url: str
    provider: AgentProvider
    skills: list[AgentSkill]
    tags: list[str] = Field(default_factory=list)

class A2AReviewInput(BaseModel):
    question: str
    task_type: TaskType | None = None
    documents: list[InputDocument] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    top_k: 4

class A2ATaskCreateRequest(BaseModel):
    task_type: Literal["legal_review"] = "legal_review"
    input: A2AReviewInput
    metadata: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str,Any]] = Field(default_factory=list)
    external_context: list[dict[str, Any]] = Field(default_factory=list)


class A2ATaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str
    artifact_url: str | None = None
    error: str | None = None


