from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.prompts import TASK_CLASSIFIER_SYSTEM
from app.agents.state import AgentState


class RouterAgent(BaseAgent):
    name = "router_agent"

    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: AgentState) -> dict:
        if state.get("task_type"):
            return {
                "task_type": state["task_type"],
                "routing_reason": "task_type provided explicitly"
            }

        payload = await self.llm.json_response(
            system=TASK_CLASSIFIER_SYSTEM,
            user=state["question"]
        )
        
        return {
            "task_type": payload["task_type"],
            "routing_reason": payload.get("reason", "")
        }