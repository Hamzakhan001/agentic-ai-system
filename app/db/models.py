from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Field, SQLModel
from sqlalchemy import JSON, Column

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class ReviewRun(SQLModel, table=True):
    id: str = Field(default_factory= lambda: str(uuid4()), primary_key=True)
    parent_run_id: str | None = Field(default=None, index=True)

    question: str 
    task_type: str | None = Field(default=None, index=True) 
    status: str = Field(default="pending", index=True)   
    top_k: int = 4


    request_payload: dict = Field(default_factory=dict, sa_column= Column(JSON))
    extracted_facts: list = Field(default_factory=list, sa_column=Column(JSON))
    critique: dict = Field(default_factory=dict, sa_column=Column(JSON))
    sources: list = Field(default_factory=list, sa_column=Column(JSON))
    external_context: list = Field(default_factory=list, sa_column=Column(JSON))

    draft_answer: str = ""
    final_answer: str = ""

    reviewer_note: str | None = None
    reviewer_name: str | None = None
    error_message: str | None = None

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)