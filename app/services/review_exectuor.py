from __future__ import annotations

from typing import Any
from sqlmodel import Session


from app.agents.graph import build_graph
from app.core.models import ReviewRequest
from app.db.models import ReviewRun
from app.services.llm import LLMService
from app.services.memory_service import MemoryService
from app.services.retrieval import SimpleRetrievalService
from app.services.review_runs import ReviewRunService
from app.services.vector_store import VectorStoreService


def _normalize_extracted_facts(raw_facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for fact in raw_facts:
        if not isinstance(fact, dict):
            continue
        

        fact_type = fact.get("type")
        value = fact.get("value")
        source_document_id = fact.get("source_document_id")
        confidence = fact.get("confidence", 0.0)

        if not isinstance(fact_type,str):
            continue
        
        if isinstance(value, list):
            value = "".join(str(item) for item in value)
        elif value is None:
            value = ""
        else: 
            value = str(value)
        
        source_document_id = str(source_document_id or "unkown")

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        if not value.strip():
            continue

        normalized.append({
            "type": fact_type,
            "value": value,
            "source_document_id": source_document_id,
            "confidence": confidence
        })
        
    return normalized


def _normalized_sources(raw_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        
        normalized.append({
            "document_id": str(source.get("document_id","unkown")),
            "title": str(source.get("title", "Untitled")),
            "snippet": str(source.get("snippet", ""))
        })

    return normalized


class ReviewExecutor:
    def __init__(self, session: Session):
        self.session = session
        self.run_service = ReviewRunService(session)

    
    async def execute(self, run: ReviewRun, body: ReviewRequest, *, eval_mode: bool = False):
        self.run_service.mark_running(run)

        llm = LLMService.for_eval() if eval_mode else LLMService()
        keyword_retriever = SimpleRetrievalService()
        vector_store = VectorStoreService() if body.document_ids else None
        memory_service = MemoryService(self.session)

        graph = build_graph(
            llm = llm,
            keyword_retriever = keyword_retriever,
            memory_service = memory_service,
            vector_store = vector_store,
        )

        result = await graph.ainvoke({
            "review_run_id": run.id,
            "case_id": run.id,
            "question": body.question,
            "task_type": body.task_type,
            "documents": body.documents,
            "document_ids": body.document_ids,
            "top_k": body.top_k,
        })

        result["extracted_facts"] = _normalize_extracted_facts(result.get("extracted_facts", []))
        result["sources"] = _normalize_sources(result.get("sources",[]))

        self.run_service.complete_run(run, result)
        return result

        
