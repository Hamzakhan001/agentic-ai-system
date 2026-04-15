from __future__ import annotations

from app.agents.prompts import TASK_CLASSIFIER_SYSTEM
from app.agents.state import AgentState


async def intake(state: AgentState, llm) -> AgentState:
    if state.get("task_type"):
        return state

    payload = await llm.json_response(
        system=TASK_CLASSIFIER_SYSTEM,
        user=state["question"],
    )
    return {**state, "task_type": payload["task_type"]}
