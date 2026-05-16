"""Multi-provider data aggregation with cross-validation and verification scoring."""

import asyncio
import time
from typing import Any

from core.provider_registry import ProviderRegistry
from core.ai_analyzer import AIAnalyzer
from core.config import Settings
from models.schemas import (
    AggregatedResult,
    SourceResult,
    ConsensusReport,
)


AGGREGATE_PROMPT = """You are a multi-source intelligence analyst.
You have received prediction market data from multiple platforms about the same topic.
Analyze the data across ALL sources and provide:

1. Cross-platform comparison — Do the prices/probabilities agree or diverge?
2. Consensus estimate — Weighted probability across all sources
3. Source reliability — Which sources are most useful for this topic
4. Key insights — What the combined picture tells us that single sources miss
5. Confidence assessment — How much trust to place in the aggregated data

Be specific about which sources agree and where they diverge.
Focus on actionable intelligence."""


class DataAggregator:
    def __init__(self, provider_registry: ProviderRegistry, ai_analyzer: AIAnalyzer, settings: Settings):
        self.providers = provider_registry
        self.analyzer = ai_analyzer
        self.settings = settings

    async def aggregate(self, request_id: str, query: str, provider_ids: list[str] | None = None) -> AggregatedResult:
        start = time.monotonic()
        all_providers = self.providers.list_all()

        if provider_ids:
            targets = [p for p in all_providers if p.provider_id in provider_ids]
        else:
            targets = all_providers

        sources = []
        results = []
        total_cost = 0

        async def fetch_from_provider(provider):
            ts = time.monotonic()
            try:
                params = {"request_id": request_id, "query": query, "limit": 5}
                result = await provider.get_data(params)
                elapsed = (time.monotonic() - ts) * 1000
                markets = len((result.data or {}).get("markets", []))
                sources.append(SourceResult(
                    provider_id=provider.provider_id,
                    provider_name=provider.name,
                    success=True,
                    market_count=markets,
                    cost_hbar=provider.cost_hbar,
                    processing_time_ms=round(elapsed, 1),
                ))
                results.append(result)
                return provider.cost_hbar
            except Exception as e:
                elapsed = (time.monotonic() - ts) * 1000
                sources.append(SourceResult(
                    provider_id=provider.provider_id,
                    provider_name=provider.name,
                    success=False,
                    cost_hbar=0,
                    processing_time_ms=round(elapsed, 1),
                    error=str(e)[:100],
                ))
                return 0

        costs = await asyncio.gather(*[fetch_from_provider(p) for p in targets])
        total_cost = sum(costs)
        elapsed_total = (time.monotonic() - start) * 1000

        successful = [s for s in sources if s.success]
        agreement = self._cross_validate(results)
        ai_analysis = None
        if self.settings.openai_api_key and results:
            merged = self._merge_results(results)
            ai_analysis = self.analyzer.analyze("aggregated", merged)

        verification = 0.0
        if successful:
            success_ratio = len(successful) / len(sources) if sources else 0
            verification = round(0.5 * agreement + 0.3 * success_ratio + 0.2 * min(len(successful) / 4, 1), 2)

        summary = f"Consulted {len(successful)}/{len(sources)} sources. "
        if agreement >= 0.8:
            summary += "High consensus across providers."
        elif agreement >= 0.5:
            summary += "Moderate agreement — some divergence detected."
        else:
            summary += "Low agreement — providers show conflicting signals."

        merged_data = self._merge_results(results)

        return AggregatedResult(
            request_id=request_id,
            query=query,
            sources=sources,
            consensus=ConsensusReport(
                agreement_score=round(agreement, 3),
                total_sources=len(sources),
                successful_sources=len(successful),
                summary=summary,
            ),
            data=merged_data,
            analysis=ai_analysis,
            verification_score=verification,
            total_cost_hbar=total_cost,
            processing_time_ms=round(elapsed_total, 1),
        )

    def _cross_validate(self, results: list) -> float:
        """Compare prices from different providers for overlapping markets.
        Returns agreement score 0.0-1.0."""
        if len(results) < 2:
            return 1.0

        all_markets = []
        for r in results:
            markets = (r.data or {}).get("markets", [])
            all_markets.append(markets)

        comparisons = 0
        agreements = 0

        for i in range(len(all_markets)):
            for j in range(i + 1, len(all_markets)):
                for mi in all_markets[i]:
                    for mj in all_markets[j]:
                        title_i = (mi.get("title") or mi.get("question", "")).lower()
                        title_j = (mj.get("title") or mj.get("question", "")).lower()
                        if self._topics_match(title_i, title_j):
                            comparisons += 1
                            price_i = mi.get("yes_price") or mi.get("price")
                            price_j = mj.get("yes_price") or mj.get("price")
                            if price_i is not None and price_j is not None:
                                diff = abs(float(price_i) - float(price_j))
                                if diff < 0.1:
                                    agreements += 1

        if comparisons == 0:
            return 0.5
        return agreements / comparisons

    def _topics_match(self, a: str, b: str) -> bool:
        """Check if two market titles refer to the same topic."""
        words_a = set(a.split())
        words_b = set(b.split())
        common = words_a & words_b
        min_len = min(len(words_a), len(words_b))
        if min_len == 0:
            return False
        return len(common) / min_len >= 0.4

    def _merge_results(self, results: list) -> dict[str, Any]:
        """Merge multiple provider results into a unified dataset."""
        all_markets = []
        seen_titles = set()

        for r in results:
            markets = (r.data or {}).get("markets", [])
            for m in markets:
                title = m.get("title") or m.get("question", "")
                key = title.lower().strip()
                if key and key not in seen_titles:
                    seen_titles.add(key)
                    all_markets.append(m)

        return {
            "aggregated": True,
            "source_count": len(results),
            "total_markets": len(all_markets),
            "markets": all_markets[:20],
        }
