from __future__ import annotations
from datetime import datetime, timezone
from sqlmodel import Session, desc, select
from app.db.memory_models import MemoryNote


def utc_now() -> datetime:
    return datetime.now(datetime.utc)


class MemoryService:
    def __init__(self, session: Session):
        self.session = session

        def load_memory(self, 
        *,
        scope_type: str, 
        scope_id: str, 
        min_importance: int=4, 
        limit:int=10) -> list[MemoryNote]:
            statement = (
                select(MemoryNote)
                .where(MemoryNote.scope_type == scope_type)
                .where(MemoryNote.scope_id == scope_id)
                .where(MemoryNote.importance >= min_importance)
                .order_by(desc(MemoryNote.importance)), desc(MemoryNote.created_at)
                .limit(limit)
            )
            return list(self.session.exec(statement))


    def save_memory_note(
        self,
        *,
        scope_type: str,
        scope_id: str,
        note_type: str,
        content: str,
        importance: int,
        source_run_id: str | None = None,
        created_by: str | None = None,
    ) -> MemoryNote:
        note = MemoryNote(
            scope_type = scope_type,
            scope_id = scope_id,
            note_type = note_type,
            content = content,
            importance = importance,
            source_run_id = source_run_id,
            created_by = created_by,
            created_at = utc_now(),
        )
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note

    def maybe_save_durable_notes_from_review(
        self,
        *,
        scope_type: str,
        scope_id: str,
        reviewer_note: str | None,
        final_answer: str,
        source_run_id: str,
        created_by: str | None = None,
    ) -> list[MemoryNote]:
        saved: list[MemoryNote] = []

        if reviewer_note and len(reviewer_note.strip()) >= 8:
            saved.append(
                self.save_memory_note(
                    scope_type = scope_type,
                    scope_id = scope_id,
                    note_type = "instruction",
                    content = review_documents.strip(),
                    importance = 5,
                    source_run_id = source_run_id,
                    created_by = created_by,
                )
            )
        
        if "prefer" in final_answer.lower() or "priority" in final_answer.lower():
            saved.append(
                self.save_memory_note(
                    scope_type = scope_type,
                    scope_id = scope_id,
                    note_type = "preference",
                    content = final_answer[:300],
                    importance = 4,
                    source_run_id = source_document_id,
                    created_by = created_by
                )
            )

            return saved