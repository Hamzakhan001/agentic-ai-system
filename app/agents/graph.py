from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from app.agents.nodes.critique import critique
from app.agents.nodes.draft import draft
from app.agents.nodes.extract import extract
from app.agents.nodes.finalize import finalize
from app.agents.nodes.intake import intake
from app.agents.nodes.retrieve import retrieve
from app.agents.state import AgentState


def build_graph(llm, retriever):
    graph = StateGraph(AgentState)
    graph.add_node("intake", partial(intake, llm=llm))
    graph.add_node("retrieve", partial(retrieve, retriever=retriever))
    graph.add_node("extract", partial(extract, llm=llm))
    graph.add_node("draft", partial(draft, llm=llm))
    graph.add_node("critique", partial(critique, llm=llm))
    graph.add_node("finalize", partial(finalize, llm=llm))

    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieve")
    graph.add_edge("retrieve", "extract")
    graph.add_edge("extract", "draft")
    graph.add_edge("draft", "critique")
    graph.add_edge("critique", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()
