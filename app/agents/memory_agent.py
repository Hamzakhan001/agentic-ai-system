from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.state import AgentState
from app.services.memory_service import MemoryService

class MemoryAgent(BaseAgent):
    name = "memory_agent"
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def run(self, state: AgentState) -> dict:
        review_run_id = state.get("review_run_id")
        if not review_run_id:
            return {"memory_contenxt": []}

        notes = self.memory_service.load_memory(
            scop_type="case",
            scope_id= review_run_id,
            min_importance=4,
            limit=10
        )

        return {
            "memory_context": [
                {
                    "note_id": note.id,
                    "note_type": note.note_type,
                    "content": note.content,
                    "importance": note.importance
                }
                for note in notes
            ]
        }

