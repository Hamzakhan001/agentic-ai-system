from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import get_settings


class GeneralWebSearchTool:

    name="general_web_search"
    def __init__(self) -> None:
        self.settings = get_settings()
    
    async def run(self, query: str, max_results: int =3) -> list[dict[str, Any]]:
        if not self.settings.tavily_api_key:
            return []

        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "tool": self.name,
                    "title": item.get("title",""),
                    "url": item.get("url",""),
                    "content":item.get("content","")
                }
                for item in data.get("results", [])
            ]

class LegalWebSearchTool:
    name="legal_web_search"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def run(self, query:str, max_results: int =3) -> list[dict[str,Any]]:
        if not self.settings.tavily_api_key:
            return []
        
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_domains": ["legislation.gov.uk", "www.legislation.gov.uk", "www.bailii.org"],

        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()

        return [
            {
                "tool": self.name,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
            for item in data.get("results",[])
        ]


class GovUkGuidanceSearchTool:
    name="govuk_guidance_search"

    def __init__(self) -> None:
        self.settings = get_settings()

    
    async def run(self, query:str, max_results: int = 3) -> list[dict[str, Any]]:
        if not self.settings.tavily_api_key:
            return []

        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_domains": ["gov.uk", "www.gov.uk"]
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()

        return [
            {
                "tool": self.name,
                "title": item.get("title",""),
                "url": item.get("url",""),
                "content": item.get("content", ""),

            }
            for item in data.get("results",[])
        ]

class CompaniesHouseLookupTool:
    name = "companies_house_lookup"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def run(self, company_name: str) -> list[dict[str, Any]]:
        if not self.settings.companies_house_api_key or not company_name.strip():
            return []

        url = "https://api.company-information.service.gov.uk/search/companies"
        auth = (self.settings.companies_house_api_key,"")

        async with httpx.AsyncClient(timeout=20.0, auth=auth) as client:
            response = await client.get(url, params={"q": company_name, "items_per_page":3})
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "tool": self.name,
                    "company_name": item.get("title", ""),
                    "company_number": item.get("company_number", ""),
                    "company_status": item.get("company_status", ""),
                    "company_type": item.get("company_type", ""),
                    "address_snippet": item.get("address_snippet", ""),
                })
        
        return results
        
class DateCalculatorTool:
    name="date_calculator"

    DATE_PATTERNS = [
        r"\b\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\b",
    ]

    NOTICE_PATTERN = r"\b(\d+)-day\b"

    async def run(self, texts: list[str]) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._calculate, texts)

    def _calculate(self, texts: list[str]) -> list[dict[str, Any]]:
        all_text = "\n".join(texts)
        base_dates = []
        for pattern in self.DATE_PATTERNS:
            base_dates.extend(re.findall(pattern, all_text))

        notice_matches = re.findall(self.NOTICE_PATTERN, all_text)
        if not base_dates and not notice_matches:
            return []

        results: list[dict[str, Any]] = []

        for date_str in base_dates:
            try:
                parsed = datetime.strptime(date_str, "%d %B %Y").replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            for notice in notice_matches:
                deadline = parsed + timedelta(days = int(notice))
                results.append(
                    {
                        "tool": self.name,
                        "base_date": date_str,
                        "notice_days": int(notice),
                        "derived_deadline": deadline.strftime("%Y-%m-%d"),
                    }
                )
        return results

