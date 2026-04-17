from __future__ import annotations

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class MemoryNote(SQLModel, table=True):
    id: str = Field(default_factory= lambda: str(uuid4()), primary_key=True)
    scope_type: str = Field(index=True)
    scope_id: str = Field(index=True)
    note_type: str = Field(index=True)
    content: str
    importance: int = Field(default=3, index=True)
    source_run_id: str | None = Field(default=None, index=True)
    created_by: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)