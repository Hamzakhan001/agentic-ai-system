from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.state import AgentState

class RetrieverAgent(BaseAgent):
    name = "retriever_agent"

    def __init__(self, keyword_retriever, vector_store=None) -> None:
        self.keyword_retriever = keyword_retriever
        self.vector_store = vector_store

    
    async def run(self, state: AgentState) -> dict:
        if state.get("documents"):
            docs = self.keyword_retriever.search(
                question = state["question"],
                documents = state["documents"],
                top_k= state.get("top_k", 4)
            )

            return {
                "retrieved_documents": docs,
                "source_ids": [doc.id for doc in docs]

            }   

        if state.get("document_ids"):
            if self.vector_store is None:
                raise RuntimeError("Vector store is required using documents ids")
            

            docs = await self.vector_store.similarity_search(
                query=state["question"],
                top_k = state.get("top_k",4),
                document_ids = state["document_ids"]
            )

            return {
                "retrieved_documents": docs,
                "source_ids": [doc.id for doc in docs]
            }

        return {
            "retrieved_documents": [],
            "source_ids": []
        }