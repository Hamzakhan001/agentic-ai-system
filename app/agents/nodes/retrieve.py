from __future__ import annotations

from app.agents.state import AgentState


async def retrieve(state: AgentState, retriever) -> AgentState:
    docs = retriever.search(
        question=state["question"],
        documents=state["documents"],
        top_k=state.get("top_k", 4),
    )
    return {**state, "retrieved_documents": docs}
