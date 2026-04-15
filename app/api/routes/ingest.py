from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile


from app.core.models import IngestResponse, IngestTextRequest
from app.services.ingestion import IngestionService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _get_ingestion_service() -> IngestionService:
    vector_store = VectorStoreService()
    return IngestionService(vector_store)


@router.post("/text", response_model=IngestResponse)
async def ingest_text(body: IngestTextRequest) -> IngestResponse:
    try:
        ingestion = _get_ingestion_service()
        return await ingestion.ingest_text(
            title = body.title,
            text = body.text,
            metadata = body.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model = IngestResponse)
async def ingest_file(file: UploadFile = File(...)) -> IngestResponse:
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        ingestion = _get_ingestion_service()
        return await ingestion.ingest_file(
            file_bytes = content,
            filename = file.filename or "upload.txt",
            metadata = {"content_type": file.content_type or ""}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))