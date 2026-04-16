from __future__ import annotations

import asyncio
import re

from app.agents.base import BaseAgent
from app.agents.state import AgentState
from app.tools.external_tools import (
    CompaniesHouseLookupTool,
    DateCalculatorTool, 
    GeneralWebSearchTool,
    GovUkGuidanceSearchTool,
    LegalWebSearchTool
)


class ResearchAgent(BaseAgent):
    name="research_agent"
    
    def __init__(self) -> None:
        self.general_search = GeneralWebSearchTool()
        self.legal_search = LegalWebSearchTool()
        self.govuk_search = GovUkGuidanceSearchTool()
        self.company_lookup = CompaniesHouseLookupTool()
        self.date_calculator = DateCalculatorTool()

    def _extract_company_candidates(self, text: str) -> list[str]:
        pattern = r"\b([A-Z][A-Za-z&,\- ]+(?:Ltd|Limited|PLC|LLP))\b"
        return list(set(re.findall(pattern,text)))


    async def run(self, state: AgentState) -> dict:
        question = state["question"]
        task_type = state["task_type"]
        docs = state.get("retrieved_documents", [])

        docs_text = [doc.text for doc in docs]
        joined_text = "\n".join(docs_text)
        lowercase_question = question.lower()

        tasks = []

        if any(term in lowercase_question for term in ["law", "legal", "compliance", "regulation", "statute"]):
            tasks.append(self.legal_search.run(question))
        
        if any(term in lowercase_question for term in ["gov", "government", "uk guidance", "regulation", "policy"]):
            tasks.append(self.govuk_search.run(question))
        
        if any(term in lowercase_question for term in ["company", "counterparty", "organisation", "organization"]):
            company_candidates = self._extract_company_candidates(joined_text + "\n" + question)
            if company_candidates:
                tasks.append(self.company_lookup.run(company_candidates[0]))
        
        if task_type in {"timeline", "next_steps", "evidence_extraction"}:
            tasks.append(self.date_calculator.run(docs_text))

        if any(term in lowercase_question for term in ["market", "background", "news", "context", "public information"]):
            tasks.append(self.general_search.run(question))
        
        if not tasks:
            return {"external_context": []}
        
        raw_results = await asyncio.gather(*tasks, return_exceptions = True)
        

        external_context = []
        for result in raw_results:
            if isinstance(result, Exception):
                print(f"Error in research agent: {result}")
                continue
            external_context.append(result)
        
        return {"external_context": external_context}
