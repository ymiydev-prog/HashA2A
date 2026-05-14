import time
from abc import abstractmethod
from typing import Any

from core.base_provider import BaseDataProvider
from models.schemas import DataResponse, RequestStatus
from providers.betting.schemas import (
    BettingMarket,
    BettingAnalysis,
    BettingQuery,
)


class BettingDataProvider(BaseDataProvider):
    niche: str = "betting"

    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term for markets"},
            "market_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific market IDs to fetch",
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Max markets to return",
            },
            "include_analysis": {
                "type": "boolean",
                "default": True,
                "description": "Run analysis on fetched markets",
            },
            "category": {
                "type": "string",
                "description": "Filter by category",
            },
            "status": {
                "type": "string",
                "enum": ["open", "closed", "resolved"],
                "description": "Filter by market status",
            },
        },
    }

    @abstractmethod
    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        ...

    @abstractmethod
    async def get_market(self, market_id: str) -> BettingMarket | None:
        ...

    async def get_data(self, params: dict[str, Any]) -> DataResponse:
        start = time.monotonic()
        query = BettingQuery(**params)
        request_id = params.get("request_id", "")

        if query.market_ids:
            markets = []
            for mid in query.market_ids:
                market = await self.get_market(mid)
                if market:
                    markets.append(market)
        else:
            markets = await self.list_markets(query)

        analysis = None
        if query.include_analysis and markets:
            analysis = self.analyze_markets(markets)

        elapsed = (time.monotonic() - start) * 1000

        return DataResponse(
            request_id=request_id,
            provider_id=self.provider_id,
            status=RequestStatus.COMPLETED,
            data={
                "platform": self.provider_id,
                "markets": [m.model_dump() for m in markets],
                "total_found": len(markets),
            },
            analysis=self._format_analysis(analysis) if analysis else None,
            raw_size_bytes=len(str(markets)),
            processing_time_ms=elapsed,
            provider_trust_score=self.reputation.trust_score,
        )

    def analyze_markets(self, markets: list[BettingMarket]) -> list[BettingAnalysis]:
        results: list[BettingAnalysis] = []
        for market in markets:
            probs = {}
            for outcome in market.outcomes:
                if outcome.price is not None:
                    probs[outcome.name] = float(f"{outcome.price:.4f}")

            if not probs:
                continue

            risks = self._identify_risks(market)
            confidence = self._calculate_confidence(market)

            results.append(
                BettingAnalysis(
                    market_id=market.market_id,
                    platform=market.platform,
                    title=market.title,
                    market_implied_probabilities=probs,
                    market_confidence=confidence,
                    risk_factors=risks,
                    reasoning=self._generate_reasoning(market),
                )
            )
        return results

    def _calculate_confidence(self, market: BettingMarket) -> str:
        if market.liquidity > 500_000:
            return "high"
        elif market.liquidity > 50_000:
            return "medium"
        elif market.liquidity > 5_000:
            return "low"
        return "very_low"

    def _generate_reasoning(self, market: BettingMarket) -> str:
        parts = []
        if market.volume > 0:
            parts.append(f"Volume: ${market.volume:,.0f}")
        if market.liquidity > 0:
            parts.append(f"Liquidity: ${market.liquidity:,.0f}")
        outcomes_str = ", ".join(
            f"{o.name} @ {o.price:.1%}" if o.price is not None else o.name
            for o in market.outcomes
        )
        if outcomes_str:
            parts.append(f"Odds: [{outcomes_str}]")
        if market.status.value == "resolved":
            parts.append(f"Resolved: {market.resolution_outcome}")
        return " | ".join(parts) if parts else "No additional data available"

    def _identify_risks(self, market: BettingMarket) -> list[str]:
        risks = []
        if market.liquidity < 10_000:
            risks.append("Low liquidity — may be difficult to trade at fair price")
        if market.volume < 1_000:
            risks.append("Low volume — price may not reflect true probability")
        if market.status.value == "resolved":
            risks.append("Market is already resolved")
        if market.status.value == "closed":
            risks.append("Market is closed for new positions")
        return risks

    def _format_analysis(self, analysis: list[BettingAnalysis]) -> str:
        if not analysis:
            return "No markets available for analysis."

        lines = [f"=== {self.name} — Market Analysis ===", ""]
        for a in analysis:
            lines.append(f"Market: {a.title}")
            for outcome, prob in a.market_implied_probabilities.items():
                lines.append(f"  {outcome}: {prob:.1%}")
            lines.append(f"  Confidence: {a.market_confidence}")
            if a.risk_factors:
                lines.append(f"  Risks: {', '.join(a.risk_factors)}")
            lines.append("")
        return "\n".join(lines)
