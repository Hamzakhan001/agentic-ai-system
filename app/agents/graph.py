from __future__ import annotations
from functools import partial
from langgraph.graph import END, StateGraph

from app.agents.critic_agent import CriticAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.extractor_agent import ExtractorAgent
from app.agents.finalizer_agent import FinalizeAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.router_agent import RouterAgent
from app.agents.state import AgentState



async def _run_agent_node(state: AgentState, agent) -> AgentState:
    updates = await agent.run(state)
    return {**state, **updates}

def _route_after_extract(state: AgentState) -> str:
    if state["task_type"] == "evidence_extraction":
        return "finalizer"
    return "drafter"

def build_graph(llm, keyword_retriever, vector_store=None):
    router_agent = RouterAgent(llm = llm)
    retriever_agent = RetrieverAgent(
        keyword_retriever = keyword_retriever,
        vector_store = vector_store
    )
    extractor_agent = ExtractorAgent(llm=llm)
    drafting_agent = DraftingAgent(llm=llm)
    critic_agent = CriticAgent(llm=llm)
    finalizer_agent = FinalizeAgent(llm=llm)
    
    graph = StateGraph(AgentState)

    graph.add_node("router", partial(_run_agent_node, agent=router_agent))
    graph.add_node("retriever", partial(_run_agent_node, agent=retriever_agent))
    graph.add_node("extractor", partial(_run_agent_node, agent=extractor_agent))
    graph.add_node("drafter", partial(_run_agent_node, agent=drafting_agent))
    graph.add_node("critic", partial(_run_agent_node, agent=critic_agent))
    graph.add_node("finalizer", partial(_run_agent_node, agent=finalizer_agent))
    

    graph.set_entry_point("router")
    graph.add_edge("router", "retriever")
    graph.add_edge("retriever", "extractor")

    graph.add_conditional_edges(
        "extractor",
        _route_after_extract,
        {
            "drafter": "drafter",
            "finalizer": "finalizer"
        }
    )

    graph.add_edge("drafter", "critic")
    graph.add_edge("critic", "finalizer")
    graph.add_edge("finalizer", END)
    
    return graph.compile()
    
    
