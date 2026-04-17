from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.state import AgentState
from app.tools.external_tools import (
    GeneralWebSearchTool,
    LegalWebSearchTool,
    GovUkGuidanceSearchTool,
    CompaniesHouseLookupTool,
    DateCalculatorTool
)

class ResearchAgent(BaseAgent):
    name = "research_agent"
    
    def __init__(self):
        self.legal_search = LegalWebSearchTool()
        self.govuk_search = GovUkGuidanceSearchTool()
        self.company_lookup = CompaniesHouseLookupTool()
        self.date_calculator = DateCalculatorTool()
        self.general_search = GeneralWebSearchTool()
    
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
            # Simple company name extraction - look for company-like terms in the text
            import re
            company_pattern = r'\b[A-Z][a-zA-Z\s&]+(?:Ltd|Limited|PLC|Inc|Corp|Corporation|LLC|LLP)\b'
            matches = re.findall(company_pattern, joined_text + "\n" + question, re.IGNORECASE)
            if matches:
                tasks.append(self.company_lookup.run(matches[0]))
        
        if task_type in {"timeline", "next_steps", "evidence_extraction"}:
            tasks.append(self.date_calculator.run(docs_text))

        if any(term in lowercase_question for term in ["market", "background", "news", "context", "public information"]):
            tasks.append(self.general_search.run(question))
        
        if not tasks:
            return {"external_context": []}

        import asyncio
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        external_context = []
        for result in raw_results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, list):
                external_context.extend(result)
            else:
                external_context.append(result)
        
        return {"external_context": external_context}
