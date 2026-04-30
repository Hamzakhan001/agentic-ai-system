from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.prompts import get_task_classifier_system
from app.agents.state import AgentState
from opentelemetry import trace



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
        prompt = get_task_classifier_system()
        span = trace.get_current_span()
        if span is not None:
            span.set_attribute("prompt.name", prompt["name"])
            span.set_attribute("prompt.tag", prompt["tag"])
            span.set_attribute("prompt.version_id", prompt["version_id"] or "fallback")
            span.set_attribute("prompt.source", prompt["source"])

        payload = await self.llm.json_response(
            system=prompt["content"],
            user=state["question"],
        )

        
        return {
            "task_type": payload["task_type"],
            "routing_reason": payload.get("reason", "")
        }