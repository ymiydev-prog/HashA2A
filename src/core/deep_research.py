"""Deep research engine — investigates questions across web, news, and social media."""

import asyncio
import json
import time
from typing import Any

import httpx
from duckduckgo_search import DDGS

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

Sources consulted:
- Web search results ({web_count} sources)
- News articles ({news_count} sources)
- Social media signals
- Prediction market data (Polymarket, Kalshi, PredictIt, Manifold)

Web findings:
{web_text}

News findings:
{news_text}

Market data:
{market_text}

Produce a structured analysis covering:

1. **Context Investigation** — What do web and news sources reveal about this topic? Key facts, dates, announcements, controversies.
2. **Social Sentiment** — What is the general sentiment on social media and forums? Bullish/bearish/neutral?
3. **Market Comparison** — How do prediction market prices compare to the research findings? Is the market correctly priced?
4. **Key Risks & Catalysts** — What events could move this market significantly?
5. **Final Verdict** — Based on ALL evidence (not just market prices), what is your probability assessment?

Be specific, cite sources, and clearly distinguish between facts found in research vs market sentiment.
"""


class DeepResearchEngine:
    def __init__(self, settings: Settings, provider_registry: ProviderRegistry, ai_analyzer: AIAnalyzer):
        self.settings = settings
        self.providers = provider_registry
        self.analyzer = ai_analyzer

    async def research(self, request_id: str, question: str) -> DeepResearchReport:
        start = time.monotonic()
        report = DeepResearchReport(request_id, question)

        web_results, news_results, market_data = await asyncio.gather(
            self._search_web(question),
            self._search_news(question),
            self._fetch_market_data(question),
        )

        report.web_results = web_results
        report.news_results = news_results
        report.market_data = market_data

        social = await self._analyze_social_signals(question, web_results)
        report.social_signals = social

        analysis = self._generate_analysis(question, report)
        report.analysis = analysis

        report.processing_time_ms = (time.monotonic() - start) * 1000
        report.status = RequestStatus.COMPLETED
        return report

    async def _search_web(self, query: str) -> list[dict]:
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, self._ddg_web, query)
            return results[:8]
        except Exception as e:
            return [{"title": "Search failed", "body": str(e)}]

    def _ddg_web(self, query: str) -> list[dict]:
        try:
            with DDGS() as ddgs:
                return [{"title": r["title"], "body": r.get("body", ""), "href": r.get("href", "")}
                        for r in ddgs.text(query, max_results=8)]
        except Exception:
            return []

    async def _search_news(self, query: str) -> list[dict]:
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, self._ddg_news, query)
            return results[:6]
        except Exception:
            return []

    def _ddg_news(self, query: str) -> list[dict]:
        try:
            with DDGS() as ddgs:
                return [{"title": r["title"], "body": r.get("body", ""), "date": r.get("date", "")}
                        for r in ddgs.news(query, max_results=6)]
        except Exception:
            return []

    async def _fetch_market_data(self, question: str) -> dict[str, Any]:
        market_data = {}
        all_providers = self.providers.list_all()

        async def fetch(p):
            try:
                result = await p.get_data({"request_id": "research", "query": question, "limit": 3})
                markets = (result.data or {}).get("markets", [])
                if markets:
                    return p.provider_id, {"name": p.name, "markets": markets[:3], "cost": p.cost_hbar}
                return p.provider_id, {"name": p.name, "markets": [], "cost": p.cost_hbar}
            except Exception as e:
                return p.provider_id, {"name": p.name, "error": str(e)}

        results = await asyncio.gather(*[fetch(p) for p in all_providers])
        for pid, data in results:
            market_data[pid] = data
        return market_data

    async def _analyze_social_signals(self, question: str, web_results: list[dict]) -> dict[str, Any]:
        social = {"sentiment": "neutral", "mentions": 0, "key_themes": []}
        combined = " ".join(r.get("body", "") for r in web_results).lower()

        positive_words = ["bullish", "likely", "expected", "announced", "confirmed", "approved"]
        negative_words = ["unlikely", "doubtful", "delayed", "rejected", "cancelled", "denied"]

        pos_count = sum(1 for w in positive_words if w in combined)
        neg_count = sum(1 for w in negative_words if w in combined)

        if pos_count > neg_count + 2:
            social["sentiment"] = "positive"
        elif neg_count > pos_count + 2:
            social["sentiment"] = "negative"
        else:
            social["sentiment"] = "mixed"

        social["mentions"] = len(web_results)
        return social

    def _generate_analysis(self, question: str, report: DeepResearchReport) -> str | None:
        api_key = self.settings.openai_api_key
        if not api_key:
            return self._fallback_analysis(question, report)

        web_text = "\n".join(
            f"- {r['title']}: {r['body'][:200]}" for r in report.web_results if r.get("body")
        ) or "No web results."
        news_text = "\n".join(
            f"- {r['title']} ({r.get('date','')}): {r['body'][:200]}"
            for r in report.news_results if r.get("body")
        ) or "No news results."
        market_text = json.dumps(report.market_data, indent=2, default=str)[:1500]

        try:
            llm = self.analyzer._get_llm()
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=RESEARCH_PROMPT.format(
                    question=question, web_count=len(report.web_results),
                    news_count=len(report.news_results),
                    web_text=web_text, news_text=news_text,
                    market_text=market_text,
                )),
                HumanMessage(content=f"Research the question: {question}"),
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            return self._fallback_analysis(question, report)

    def _fallback_analysis(self, question: str, report: DeepResearchReport) -> str:
        lines = [f"Research Report: {question}", ""]
        if report.web_results:
            lines.append("Web Findings:")
            for r in report.web_results[:4]:
                lines.append(f"  • {r.get('title', '')[:80]}")
        lines.append("")
        if report.news_results:
            lines.append("Recent News:")
            for r in report.news_results[:3]:
                lines.append(f"  • {r.get('title', '')[:80]}")
        lines.append("")
        lines.append(f"Social Sentiment: {report.social_signals.get('sentiment', 'neutral')}")
        lines.append("")
        market_data = report.market_data or {}
        for pid, data in market_data.items():
            m = data.get("markets", [])
            if m:
                q = m[0].get("question", m[0].get("title", "?"))
                p = m[0].get("yes_price", "?")
                lines.append(f"  {data.get('name', pid)}: {q[:50]} → {p}")
        return "\n".join(lines)
