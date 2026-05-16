"""Deep research engine — investigates questions using OpenAI web_search tool."""

import asyncio
import json
import time
from typing import Any

import httpx
from openai import OpenAI

from core.config import Settings
from core.ai_analyzer import AIAnalyzer
from core.provider_registry import ProviderRegistry
from models.schemas import RequestStatus


class DeepResearchReport:
    def __init__(self, request_id: str, question: str):
        self.request_id = request_id
        self.question = question
        self.status = RequestStatus.PROCESSING
        self.web_results: list[dict] = []
        self.news_results: list[dict] = []
        self.social_signals: dict[str, Any] = {}
        self.market_data: dict[str, Any] | None = None
        self.analysis: str | None = None
        self.processing_time_ms: float | None = None
        self.proof_tx_id: str | None = None
        self.audit_topic_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "question": self.question,
            "status": self.status.value,
            "sources": {
                "web": len(self.web_results),
                "news": len(self.news_results),
            },
            "social_signals": self.social_signals,
            "market_data": self.market_data,
            "analysis": self.analysis,
            "processing_time_ms": self.processing_time_ms,
            "proof_tx_id": self.proof_tx_id,
            "audit_topic_id": self.audit_topic_id,
        }


RESEARCH_PROMPT = """You are a world-class investigative analyst. Your task is to analyze the gathered intelligence about a prediction market question and produce a comprehensive research report.

Question: {question}

Web search results:
{web_text}

Prediction market data:
{market_text}

Produce a structured analysis covering:

1. **Context Investigation** — What does the web search reveal? Key facts, dates, announcements, controversies.
2. **Market Comparison** — How do prediction market prices compare to the research findings?
3. **Key Risks & Catalysts** — What events could move this market significantly?
4. **Final Verdict** — Based on ALL evidence, what is your probability assessment?

Be specific, cite sources, and clearly distinguish between facts found in research vs market prices.
"""


class DeepResearchEngine:
    def __init__(self, settings: Settings, provider_registry: ProviderRegistry, ai_analyzer: AIAnalyzer):
        self.settings = settings
        self.providers = provider_registry
        self.analyzer = ai_analyzer
        self._client: OpenAI | None = None

    def _get_openai(self) -> OpenAI | None:
        if self._client is None and self.settings.openai_api_key:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    async def research(self, request_id: str, question: str) -> DeepResearchReport:
        start = time.monotonic()
        report = DeepResearchReport(request_id, question)

        oai = self._get_openai()
        if oai:
            web_results, market_data = await asyncio.gather(
                self._search_web_ai(oai, question),
                self._fetch_market_data(question),
            )
        else:
            web_results, market_data = [], {}

        report.web_results = web_results
        report.market_data = market_data
        report.social_signals = self._analyze_social_signals(web_results)
        report.analysis = self._generate_analysis(question, report)

        report.processing_time_ms = (time.monotonic() - start) * 1000
        report.status = RequestStatus.COMPLETED
        return report

    async def _search_web_ai(self, client: OpenAI, query: str) -> list[dict]:
        """Use OpenAI web_search tool to find and analyze content."""
        try:
            resp = await asyncio.to_thread(
                client.responses.create,
                model=self.settings.langchain_model,
                input=f"Research this question thoroughly. Find recent news, facts, and evidence: {query}",
                tools=[{"type": "web_search"}],
            )
            results = []
            for item in resp.output:
                if getattr(item, 'type', '') == 'message':
                    for c in getattr(item, 'content', []):
                        if hasattr(c, 'text') and c.text:
                            results.append({
                                "title": f"OpenAI web_search results for: {query[:50]}",
                                "body": c.text[:1000],
                                "href": "",
                                "ai_generated": True,
                            })
            return results[:5]
        except Exception:
            return []

    async def _fetch_market_data(self, question: str) -> dict[str, Any]:
        market_data = {}
        all_providers = self.providers.list_all()

        async def fetch(p):
            try:
                result = await p.get_data({"request_id": "research", "query": question, "limit": 3})
                markets = (result.data or {}).get("markets", [])
                return p.provider_id, {"name": p.name, "markets": markets[:3], "cost": p.cost_hbar}
            except Exception as e:
                return p.provider_id, {"name": p.name, "error": str(e)}

        results = await asyncio.gather(*[fetch(p) for p in all_providers])
        for pid, data in results:
            market_data[pid] = data
        return market_data

    def _analyze_social_signals(self, web_results: list[dict]) -> dict[str, Any]:
        social = {"sentiment": "neutral", "mentions": 0}
        combined = " ".join(r.get("body", "") for r in web_results).lower()
        positive_words = ["bullish", "likely", "expected", "announced", "confirmed", "approved"]
        negative_words = ["unlikely", "doubtful", "delayed", "rejected", "cancelled", "denied"]
        pos = sum(1 for w in positive_words if w in combined)
        neg = sum(1 for w in negative_words if w in combined)
        if pos > neg + 2:
            social["sentiment"] = "positive"
        elif neg > pos + 2:
            social["sentiment"] = "negative"
        else:
            social["sentiment"] = "mixed"
        social["mentions"] = len(web_results)
        return social

    def _generate_analysis(self, question: str, report: DeepResearchReport) -> str | None:
        api_key = self.settings.openai_api_key
        if not api_key:
            return None

        web_text = "\n".join(
            f"- [{r['title']}]({r.get('href','')}): {r['body'][:400]}"
            for r in report.web_results if r.get("body")
        ) or "No web results."
        market_text = json.dumps(report.market_data, indent=2, default=str)[:1500]

        try:
            llm = self.analyzer._get_llm()
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=RESEARCH_PROMPT.format(
                    question=question,
                    web_text=web_text,
                    market_text=market_text,
                )),
                HumanMessage(content=f"Research: {question}"),
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception:
            return None
