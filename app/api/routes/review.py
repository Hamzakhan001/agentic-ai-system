from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session

from app.agents.graph import build_graph
from app.core.models import CritiqueResult, ExtractedFact, ReviewRequest, ReviewResponse, SourceSnippet
from app.core.observability import get_tracer
from app.db.session import get_session
from app.services.llm import LLMService
from app.services.memory_service import MemoryService
from app.services.retrieval import SimpleRetrievalService
from app.services.review_runs import ReviewRunService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/review", tags=["review"])
tracer = get_tracer("agentic-legal-review.routes.review")


def _normalize_extracted_facts(raw_facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for fact in raw_facts:
        if not isinstance(fact, dict):
            continue

        fact_type = fact.get("type")
        value = fact.get("value")
        source_document_id = fact.get("source_document_id")
        confidence = fact.get("confidence", 0.0)

        if not isinstance(fact_type, str):
            continue

        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        elif value is None:
            value = ""
        else:
            value = str(value)

        if source_document_id is None:
            source_document_id = "unknown"
        else:
            source_document_id = str(source_document_id)

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        if not value.strip():
            continue

        normalized.append(
            {
                "type": fact_type,
                "value": value,
                "source_document_id": source_document_id,
                "confidence": confidence,
            }
        )

    return normalized


def _normalize_sources(raw_sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []

    for source in raw_sources:
        if not isinstance(source, dict):
            continue

        document_id = str(source.get("document_id", "unknown"))
        title = str(source.get("title", "Untitled"))
        snippet = str(source.get("snippet", ""))

        normalized.append(
            {
                "document_id": document_id,
                "title": title,
                "snippet": snippet,
            }
        )

    return normalized


@router.post("", response_model=ReviewResponse)
async def review_documents(
    body: ReviewRequest,
    session: Session = Depends(get_session),
    x_eval_mode: str | None = Header(default=None),
) -> ReviewResponse:
    with tracer.start_as_current_span("review.run") as span:
        span.set_attribute("review.question", body.question)
        span.set_attribute("review.task_type", body.task_type or "auto")
        span.set_attribute("review.document_ids_count", len(body.document_ids))
        span.set_attribute("review.inline_documents_count", len(body.documents))
        span.set_attribute("review.top_k", body.top_k)
        span.set_attribute("review.eval_mode", (x_eval_mode or "").lower() == "true")

        run_service = ReviewRunService(session)
        run = run_service.create_run(body)
        span.set_attribute("review.run_id", run.id)
        run_service.mark_running(run)

        try:
            llm = LLMService.for_eval() if (x_eval_mode or "").lower() == "true" else LLMService()
            keyword_retriever = SimpleRetrievalService()
            vector_store = VectorStoreService() if body.document_ids else None
            memory_service = MemoryService(session)

            graph = build_graph(
                llm=llm,
                keyword_retriever=keyword_retriever,
                memory_service=memory_service,
                vector_store=vector_store,
            )

            result = await graph.ainvoke(
                {
                    "review_run_id": run.id,
                    "case_id": run.id,
                    "question": body.question,
                    "task_type": body.task_type,
                    "documents": body.documents,
                    "document_ids": body.document_ids,
                    "top_k": body.top_k,
                }
            )

            normalized_facts = _normalize_extracted_facts(result.get("extracted_facts", []))
            normalized_sources = _normalize_sources(result.get("sources", []))

            result["extracted_facts"] = normalized_facts
            result["sources"] = normalized_sources

            run_service.complete_run(run, result)

            span.set_attribute("review.final_task_type", result.get("task_type", ""))
            span.set_attribute("review.extracted_facts_count", len(normalized_facts))
            span.set_attribute("review.sources_count", len(normalized_sources))

            critique_payload = result.get(
                "critique",
                {"verdict": "pass", "issues": [], "missing_information": []},
            )

            if not isinstance(critique_payload, dict):
                critique_payload = {"verdict": "pass", "issues": [], "missing_information": []}

            if critique_payload.get("verdict") not in {"pass", "revise"}:
                critique_payload["verdict"] = "pass"

            critique_payload.setdefault("issues", [])
            critique_payload.setdefault("missing_information", [])

            return ReviewResponse(
                task_type=result["task_type"],
                extracted_facts=[ExtractedFact(**fact) for fact in normalized_facts],
                draft_answer=result.get("draft_answer", ""),
                critique=CritiqueResult(**critique_payload),
                final_answer=result.get("final_answer", ""),
                sources=[SourceSnippet(**source) for source in normalized_sources],
            )
        except Exception as exc:
            run_service.fail_run(run, str(exc))
            span.record_exception(exc)
            raise HTTPException(status_code=500, detail=str(exc))
