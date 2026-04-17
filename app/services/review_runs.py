from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, desc, select

from app.core.models import ReviewRequest
from app.db.models import ReviewRun


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class ReviewRunService:
    def __init__(self, session: Session):
        self.session = session

    def create_run(self, body: ReviewRequest, *, parent_run_id: str | None = None, reviewer_note: str | None, reviewer_name: str | None = None) -> ReviewRun:
        run = ReviewRun(
            parent_run_id = parent_run_id,
            question = body.question,
            task_type = body.task_type,
            top_k = body.top_k,
            status="pending",
            request_payload=body.model_dump(),
            reviewer_note = reviewer_note,
            reviewer_name = reviewer_name,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_running(self, run:ReviewRun) -> ReviewRun:
        run.status = "running"
        run.updated_at = utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def complete_run(self, run:ReviewRun, result:dict) -> ReviewRun:
        run.task_type = result.get("task_type", run.task_type)
        run.status = "completed"
        run.extracted_facts = result.get("extracted_facts", [])
        run.draft_answer = result.get("draft_answer", "")
        run.critique= result.get("critique", {})
        run.final_answer = result.get("final_answer", "")
        run.sources = result.get("sources", [])
        run.external_context = result.get("external_context",[])
        run.updated_at = utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def approve_run(self, run: ReviewRun, reviewer_name: str, reviewer_note: str | None) -> ReviewRun:
        run.status = "approved"
        run.reviewer_name = reviewer_name
        run.reviewer_note = reviewer_note
        run.updated_at = utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def fail_run(self, run: ReviewRun, error_message: str) -> ReviewRun:
        run.status = "failed"
        run.error_message = error_message
        run.updated_at = utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def request_revision(self, run: ReviewRun, reviewer_name: str, reviewer_note: str) -> ReviewRun:
        run.status = "revision_requested"
        run.reviewer_name = reviewer_name
        run.reviewer_note = reviewer_note
        run.updated_at = utcnow()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_run(self, run_id: str) -> ReviewRun:
        run = self.session.get(ReviewRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Review run not found")
        return run

    def list_runs(self, limit: int = 50) -> list[ReviewRun]:
        statement = select(ReviewRun).order_by(desc(ReviewRun.created_at)).limit(limit)
        return list(self.session.exec(statement))