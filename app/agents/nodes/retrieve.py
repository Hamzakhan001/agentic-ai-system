from __future__ import annotations

from app.agents.state import AgentState


async def retrieve(state: AgentState, keyword_retriever, vector_store=None) -> AgentState:
    if state.get("document"):
        docs = keyword_retriever.search(
            question = state["question"],
            documents = state["documents"],
            top_k= state.get("top_k", 4),
        )
        return {
            **state, 
            "retrieved_docs": docs
        }

    if state.get("document_ids"):
        if vector_store is None:
            raise RuntimeError("Vector store is required")
        docs = await vector_store.similarity_search(
            query=state["question"],
            top_k=state.get("top_k",4),
            document_ids = state["document_ids"],
        )

        return {**state, "retrieved_documents": docs}
    
    return {**state, "retrieved_documents": []}

