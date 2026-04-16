from __future__ import annotations

import io
import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.models import IngestResponse
from app.services.vector_store import VectorStoreService


class IngestionService:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".csv"}
    def __init__(self, vector_store: VectorStoreService):
        self.settings = get_settings()
        self.vector_store = vector_store
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators = ["\n\n", "\n", ".", " ", ""]
        )
        
    
    async def ingest_text(
        self,
        title: str,
        text: str,
        metadata: dict | None = None,
    ) -> IngestResponse:
        document_id = str(uuid.uuid4())
        chunks = self._build_chunks(
            document_id = document_id,
            title = title,
            text = text,
            metadata = metadata or {}
        )

        await self.vector_store.upsert_chunks(chunks)
        return IngestResponse(document_id=document_id, title=title, chunks = len(chunks))
    
    async def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: dict | None = None,
    ) -> IngestResponse:
        suffix = Path(filename).suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        if suffix == ".pdf":
            text = self._extract_text_from_pdf(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")

        document_id = str(uuid.uuid4())
        chunks = self._build_chunks(
            document_id=document_id,
            title=filename,
            text=text,
            metadata=metadata or {}
        )

        await self.vector_store.upsert_chunks(chunks)
        return IngestResponse(document_id=document_id, title=filename, chunks=len(chunks))


    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        pdf = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    def _build_chunks(
        self,
        document_id: str,
        title: str,
        text: str,
        metadata: dict
    ) -> list[dict]:
        text = text[: self.settings.max_document_chars]
        split_texts = self.splitter.split_text(text)
        chunks = []

        for idx, chunk_text in enumerate(split_texts):
            chunks.append({
                "document_id": document_id,
                "title": title,
                "chunk_index": idx,
                "text": chunk_text,
                "metadata": metadata,
            })

        return chunks