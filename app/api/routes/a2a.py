from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from app.core.a2a_models import (
    A2AArtifact,
    A2ATaskCreateRequest,
    A2ATaskStatusResponse,
    A2ATaskStatusResponse,
    AgentAuthentication,
    AgentCard,
    AgentProvider,
    AgentSkill
)


from app.core.config import get_settings
from app.core.models import ReviewRequest
from app.db.models import ReviewRun
from app.db.session import engine
from app.services.review_executor import ReviewExecutor
from app.services.review_runs import ReviewRunService

well_known_router = APIRouter(tags=["a2a"])
router = APIRouter(prefix="/a2a", tags=["a2a"])


def _build_agent_card() -> AgentCard:
    settings = get_settings()
    return AgentCard(
        name = settings.agent_name,
        description = settings.agent_descripiton,
        version = settings.agent_version,
        url=f"{settings.public_base_url}{settings.api_prefix}/a2a",
        provider = AgentProvider(
            organization_id=settings.agent_organization_id,
            organization_name=settings.agent_organization_name
        )
        authentication = AgentAuthentication(type="none"),
        skills = [
            AgentSkill(
                id="contract_review",
                name="Contract Review",
                description = "Reviews legal and contractual text for risks and summaries",
                tags=["legal", "contract", "review"]
            ),
            AgentSkill(
                id="risk_review",
                name="Risk Review",
                description="Flags risks, issues, and missing information in supplied legal material.",
                tags=["legal", "risk", "compliance"],
            ),
            AgentSkill(
                id="evidence_extraction",
                name="Evidence Extraction",
                description="Extracts factual evidence and supporting snippets from legal documents.",
                tags=["legal", "evidence", "extraction"],
            ),
            AgentSkill(
                id="timeline_generation",
                name="Timeline Generation",
                description="Builds structured legal timelines from supplied materials.",
                tags=["legal", "timeline"],
            ),

        ],
        tags = ["legal", "review", "contracts", "agentic-ai"]

    )

async def _run_review_task(task_id: str, body: ReviewRequest)-> None:
    with Session(engine) as session:
        run_service = ReviewRunService(session)
        run = run_service.get_run(task_id)
        executor = ReviewExecutor(session)

        try:
            await executor.execute(run, body)
        except Exception as exc:
            run_service.fail_run(run, str(exc))

@well_known_router.get("/.well-known/agent-card.json", response_model = AgentCard, include_in_schema = False)
def public_agent_card() -> AgentCard:
    return _build_agent_card()

@router.get("/agent-card", response_model = AgentCard)
def api_agent_card() -> AgentCard:
    return _build_agent_card()

@router.post("/tasks", response_model = A2ATaskCreateRequest, status_code = 202)
async def create_a2a_task(body: A2ATaskCreateRequest) -> A2ATaskCreateResponse:
    review_request = ReviewRequest(
        question = body.input.question,
        task_type = body.input.task_type,
        documents = body.input.documents,
        document_ids = body.input.document_ids,
        top_k = body.input.top_k,
    )

    with Session(engine) as session:
        run_service = ReviewRunService(session)
        run = run_service.create_run(review_request)

    asyncio.create_task(_run_review_task(run.id, review_request))

    settings = get_settings()
    return A2ATaskCreateResponse(
        task_id = run.id,
        status = "accepted",
        status_url = f"{settings.public_base_url}{settings.api_prefix}/a2a/tasks/{run.id}"
        artifact_url = f"{settings.public_base_url}{settings.api_prefix}/a2a/tasks/{run.id}/artifact",
    )

@router.get("/tasks/{task_id}", response_model=A2ATaskStatusResponse)
def get_a2a_task(task_id: str) -> A2ATaskStatusResponse:
    with Session(engine) as session:
        run = ReviewRunService(session).get_run(task_id)

    settings = get_settings()
    artifact_url = f"{settings.public_base_url}{settings.api_prefix}/a2a/tasks/{run.id}/artifact"
    

    message_map = {
        "pending": "Task accepted and waiting to start",
        "running": "Task is currently running",
        "completed": "Task completed successfully.",
        "approved": "Task was approved after completion.",
        "revision_requested": "Task requires human revision.",
        "failed": "Task failed.",
    }

    return A2ATaskStatusResponse(
        task_id=run.id,
        status=run.status,
        message=message_map.get(run.status, "Unknown task status."),
        artifact_url=artifact_url,
        error=run.error_message,
    )


@router.get("/tasks/{task_id}/artifact", response_model=A2AArtifact)
def get_a2a_artifact(task_id: str) -> A2AArtifact:
    with Session(engine) as session:
        run: ReviewRun = ReviewRunService(session).get_run(task_id)

    if run.status not in {"completed", "approved"}:
        raise HTTPException(status_code=409, detail="Task is not finished yet")

    return A2AArtifact(
        task_id=run.id,
        final_answer=run.final_answer,
        extracted_facts=run.extracted_facts or [],
        critique=run.critique or {},
        sources=run.sources or [],
        external_context=run.external_context or [],
    )