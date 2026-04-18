from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile


from app.core.models import IngestResponse, IngestTextRequest
from app.core.observability import get_tracer
from app.services.ingestion import IngestionService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/ingest", tags=["ingest"])
tracer = get_tracer("agentic-legal-review.routes.ingest")


def _get_ingestion_service() -> IngestionService:
    vector_store = VectorStoreService()
    return IngestionService(vector_store)


@router.post("/text", response_model=IngestResponse)
async def ingest_text(body: IngestTextRequest) -> IngestResponse:
    with tracer.start_as_current_span("ingest.text") as span:
        span.set_attribute("document.title", body.title)
        span.set_attribute("document.text_length", len(body.text))
        try:
            ingestion = _get_ingestion_service()
            response = await ingestion.ingest_text(
                title = body.title,
                text = body.text,
                metadata = body.metadata
            )
            span.set_attribute("document.id", response.document_id)
            span.set_attribute("document.chunks", response.chunks)
            return response
        except Exception as e:
            span.record_exception(e)
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model = IngestResponse)
async def ingest_file(file: UploadFile = File(...)) -> IngestResponse:
    with tracer.start_as_current_span("ingest.file") as span:
        span.set_attribute("file.name", file.filename or "upload.txt")
        span.set_attribute("file.content_type", file.content_type or "")
        try:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Empty file")
            span.set_attribute("file.bytes", len(content))

            ingestion = _get_ingestion_service()
            response = await ingestion.ingest_file(
                file_bytes = content,
                filename = file.filename or "upload.txt",
                metadata = {"content_type": file.content_type or ""}
            )
            span.set_attribute("document.id", response.document_id)
            span.set_attribute("document.chunks", response.chunks)
            return response
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            raise HTTPException(status_code=500, detail=str(e))
