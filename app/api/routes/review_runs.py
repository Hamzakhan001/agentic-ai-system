from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.agents.graph import build_graph
from app.core.models import ApproveRunRequest, ReviewRequest, ReviewRunDetail, ReviewRunSummary, ReviseRunRequest
from app.db.session import get_session
from app.services.llm import LLMService
from app.services.retrieval import SimpleRetrievalService
from app.services.review_runs import ReviewRunService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/review-runs", tags=["review-runs"])


def _to_summary(run) -> ReviewRunSummary:
    return ReviewRunSummary(
        id=run.id,
        parent_run_id=run.parent_run_id,
        question=run.question,
        task_type=run.task_type,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _to_detail(run) -> ReviewRunDetail:
    return ReviewRunDetail(
        id=run.id,
        parent_run_id=run.parent_run_id,
        question=run.question,
        task_type=run.task_type,
        status=run.status,
        top_k=run.top_k,
        reviewer_note=run.reviewer_note,
        error_message=run.error_message,
        extracted_facts=run.extracted_facts,
        draft_answer=run.draft_answer,
        critique=run.critique,
        final_answer=run.final_answer,
        sources=run.sources,
        external_context=run.external_context,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.get("", response_model=list[ReviewRunSummary])
def list_review_runs(limit: int = 50, session: Session = Depends(get_session)):
    service = ReviewRunService(session)
    return [_to_summary(run) for run in service.list_runs(limit=limit)]


@router.get("/{run_id}", response_model=ReviewRunDetail)
def get_review_run(run_id: str, session: Session = Depends(get_session)):
    service = ReviewRunService(session)
    run = service.get_run(run_id)
    return _to_detail(run)


@router.post("/{run_id}/approve", response_model=ReviewRunDetail)
def approve_review_run(run_id: str, body: ApproveRunRequest, session: Session = Depends(get_session)):
    service = ReviewRunService(session)
    run = service.get_run(run_id)
    run = service.approve_run(run, reviewer_name=body.reviewer_name, reviewer_note=body.reviewer_note)
    return _to_detail(run)


@router.post("/{run_id}/revise", response_model=ReviewRunDetail)
async def revise_review_run(run_id: str, body: ReviseRunRequest, session: Session = Depends(get_session)):
    service = ReviewRunService(session)
    original_run = service.get_run(run_id)
    service.request_revision(original_run, reviewer_name=body.reviewer_name, reviewer_note=body.instruction)

    if not body.rerun:
        return _to_detail(original_run)

    request_payload = dict(original_run.request_payload or {})
    documents = request_payload.get("documents", [])
    document_ids = request_payload.get("document_ids", [])
    top_k = request_payload.get("top_k", original_run.top_k)

    revised_question = (
        f"{original_run.question}\n\n"
        f"Reviewer revision instruction: {body.instruction}"
    )

    rerun_request = ReviewRequest(
        question=revised_question,
        task_type=original_run.task_type,
        documents=documents,
        document_ids=document_ids,
        top_k=top_k,
    )

    child_run = service.create_run(
        rerun_request,
        parent_run_id=original_run.id,
        reviewer_note=body.instruction,
        reviewer_name=body.reviewer_name,
    )
    service.mark_running(child_run)

    try:
        llm = LLMService()
        keyword_retriever = SimpleRetrievalService()
        vector_store = VectorStoreService() if rerun_request.document_ids else None

        graph = build_graph(
            llm=llm,
            keyword_retriever=keyword_retriever,
            vector_store=vector_store,
        )

        result = await graph.ainvoke(
            {
                "review_run_id": child_run.id,
                "question": rerun_request.question,
                "task_type": rerun_request.task_type,
                "documents": rerun_request.documents,
                "document_ids": rerun_request.document_ids,
                "top_k": rerun_request.top_k,
            }
        )

        child_run = service.complete_run(child_run, result)
        return _to_detail(child_run)
    except Exception as exc:
        service.fail_run(child_run, str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
