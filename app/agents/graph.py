from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph
from opentelemetry.trace import Status, StatusCode

from app.agents.critic_agent import CriticAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.extractor_agent import ExtractorAgent
from app.agents.finalizer_agent import FinalizeAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.research_agent import ResearchAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.router_agent import RouterAgent
from app.agents.state import AgentState
from app.core.observability import get_tracer


tracer = get_tracer("agentic-legal-review.graph")


async def _run_agent_node(state: AgentState, agent) -> AgentState:
    with tracer.start_as_current_span(f"agent.{agent.name}") as span:
        span.set_attribute("agent.name", agent.name)
        span.set_attribute("review.run_id", state.get("review_run_id", ""))
        span.set_attribute("review.case_id", state.get("case_id", ""))
        span.set_attribute("review.task_type", state.get("task_type", "") or "")
        try:
            updates = await agent.run(state)
            span.set_attribute("agent.updated_keys", ",".join(sorted(updates.keys())))
            return {**state, **updates}
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def _route_after_extract(state: AgentState) -> str:
    if state["task_type"] == "evidence_extraction":
        return "finalizer"
    return "drafter"


def build_graph(llm, keyword_retriever, memory_service, vector_store=None):
    router_agent = RouterAgent(llm=llm)
    retriever_agent = RetrieverAgent(
        keyword_retriever=keyword_retriever,
        vector_store=vector_store,
    )
    research_agent = ResearchAgent()
    memory_agent = MemoryAgent(memory_service=memory_service)
    extractor_agent = ExtractorAgent(llm=llm)
    drafting_agent = DraftingAgent(llm=llm)
    critic_agent = CriticAgent(llm=llm)
    finalize_agent = FinalizeAgent(llm=llm)

    graph = StateGraph(AgentState)

    graph.add_node("router", partial(_run_agent_node, agent=router_agent))
    graph.add_node("retriever", partial(_run_agent_node, agent=retriever_agent))
    graph.add_node("researcher", partial(_run_agent_node, agent=research_agent))
    graph.add_node("memory_loader", partial(_run_agent_node, agent=memory_agent))
    graph.add_node("extractor", partial(_run_agent_node, agent=extractor_agent))
    graph.add_node("drafter", partial(_run_agent_node, agent=drafting_agent))
    graph.add_node("critic", partial(_run_agent_node, agent=critic_agent))
    graph.add_node("finalizer", partial(_run_agent_node, agent=finalize_agent))

    graph.set_entry_point("router")
    graph.add_edge("router", "retriever")
    graph.add_edge("retriever", "researcher")
    graph.add_edge("researcher", "memory_loader")
    graph.add_edge("memory_loader", "extractor")

    graph.add_conditional_edges(
        "extractor",
        _route_after_extract,
        {
            "drafter": "drafter",
            "finalizer": "finalizer",
        },
    )

    graph.add_edge("drafter", "critic")
    graph.add_edge("critic", "finalizer")
    graph.add_edge("finalizer", END)

    return graph.compile()
