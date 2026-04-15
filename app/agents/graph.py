form __future__ import annotations

from functools import partial

from langgraph.gragph import END, StateGraph

from app.agents.nodes.critique import critique
from app.agents.nodes.draft import (
    draft_summary,
    draft_timeline,
    draft_risk_review,
    draft_next_steps
)
from app.agents.nodes.extract import extract
from app.agents.nodes.finalize import finalize
from app.agents.nodes.intake import intake
from app.agents.nodes.retrieve import retrieve
from app.agents.state import AgentState


def _route_after_extract(state: AgentState) -> str:
    task_type = state["task_type"]

    if task_type == "summary":
        return "draft_summary"
    elif task_type == "timeline":
        return "draft_timeline"
    elif task_type == "risk_review":
        return "draft_risk_review"
    elif task_type == "next_steps":
        return "draft_next_steps"
    else:
        return "finalize"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intake", partial(intake, llm=llm))
    graph.add_node("retrieve", partial(retrieve, llm=llm))
    graph.add_node("extract", partial(extract, llm=llm))

    graph.add_node("draft_summary", partial(draft_summary, llm =llm))
    graph.add_node("draft_timeline", partial(draft_timeline, llm=llm))
    graph.add_node("draft_risk_review", partial(draft_risk_review, llm=llm))
    graph.add_node("draft_next_steps", partial(draft_next_steps, llm=llm))

    graph.add_node("critque", partial(critique, llm=llm))
    graph.add_node("finalize", partial(finalize, llm=llm))

    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieve")
    graph.add_edge("retrieve", "extract")


    graph.add_conditional_edges("extract",
     _route_after_extract,
     {
        "draft_summary": "draft_summary",
        "draft_timeline": "draft_timeline",
        "draft_risk_review": "draft_risk_review",
        "draft_next_steps": "draft_next_steps",
        "finalize": "finalize"
     },
     )

     graph.add_edge("draft_summary", "critique")
     graph.add_edge("draft_timeline", "critique")
     graph.add_edge("draft_risk_review", "critique")
     graph.add_edge("draft_next_steps", "critique")
     graph.add_edge("critique", "finalize")
     graph.add_edge("finalize", END)
     return graph.compile()
