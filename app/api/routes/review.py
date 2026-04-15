from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.graph import build_graph
from app.core.models import CritiqueResult, ExtractedFact, ReviewRequest, ReviewResponse, SourceSnippet
from app.services.llm import LLMService
from app.services.retrieval import SimpleRetrievalService

router = APIRouter(prefix="/review", tags=["review"])


@router.post("", response_model=ReviewResponse)
async def review_documents(body: ReviewRequest) -> ReviewResponse:
    try:
        llm = LLMService()
        retriever = SimpleRetrievalService()
        graph = build_graph(llm=llm, retriever=retriever)
        result = await graph.ainvoke(
            {
                "question": body.question,
                "task_type": body.task_type,
                "documents": body.documents,
                "top_k": body.top_k,
            }
        )
        return ReviewResponse(
            task_type=result["task_type"],
            extracted_facts=[ExtractedFact(**fact) for fact in result.get("extracted_facts", [])],
            draft_answer=result.get("draft_answer", ""),
            critique=CritiqueResult(**result.get("critique", {"verdict": "pass", "issues": [], "missing_information": []})),
            final_answer=result.get("final_answer", ""),
            sources=[SourceSnippet(**source) for source in result.get("sources", [])],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
