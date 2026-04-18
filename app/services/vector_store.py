from __future__ import annotations

import time
import uuid

from openai import AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings
from app.core.models import InputDocument
from app.core.logging import logger

class VectorStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.pinecone_api_key:
            raise RuntimeError("Pinecone API key is not configured")
        if not self.settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured")

        self.pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.async_openai = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self._ensure_index()

    def _ensure_index(self) -> None:
        existing_names = [idx.name for idx in self.pc.list_indexes()]

        if self.settings.pinecone_index_name not in existing_names:
            logger.info("creating_pinecone_index", index_name=self.settings.pinecone_index_name)

            self.pc.create_index(
                name = self.settings.pinecone_index_name,
                dimensions = self.settings.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.settings.pinecone_region
                )
            )
            while not self.pc.describe_index(self.settings.pinecone_index_name).status["ready"]:
                time.sleep(1)


    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self.async_openai.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=texts
        )
        sorted_data = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in sorted_data]
    

    async def upsert_chunks(self, chunks: list[dict]) -> list[str]:
        if not chunks:
            return []

        index = self.pc.Index(self.settings.pinecone_index_name)

        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self._embed_texts(texts)
        ids = [str(uuid.uuid4()) for _ in chunks]

        vectors = []
        for i,chunk in enumerate(chunks):
            vectors.append({
                "id":ids[i],
                "values": embeddings[i],
                "metadata": {
                    "document_id": chunk["document_id"],
                    "title": chunk["title"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    **chunk.get("metadata", {})
                }

            })

        index.upsert(vectors=vectors)
        return ids

    async def similarity_search(
        self,
        query: str,
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[InputDocument]:
        index = self.pc.Index(self.settings.pinecone_index_name)
        query_embedding = await self._embed_texts([query])

        filter_payload = None
        if document_ids:
            filter_payload = {"document_id": {"$in": document_ids}}


        results = index.query(
            vector = query_embedding[0],
            top_k = top_k,
            include_metadata = True,
            filter = filter_payload
        )

        docs: list[InputDocument] = []
        for match in results.matches:
            metadata = match.metadata or {}
            docs.append(
                InputDocument(
                    id=metadata.get("document_id", ""),
                    title=metadata.get("title", ""),
                    text=metadata.get("text", ""),
                    metadata=metadata
                )
            )
        
        return docs




