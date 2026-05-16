"""Verified data feed engine — oracle-style aggregation.

Design follows Chainlink/Pyth principles:
- Median aggregation (robust to outliers)
- Confidence intervals from interquartile range
- Source weighting by reputation
- Deterministic, verifiable output
"""

import asyncio
import statistics
import time
from typing import Any

from core.config import Settings
from core.provider_registry import ProviderRegistry
from models.schemas import (
    VerifiedDataFeed,
    VerifiedPricePoint,
    SourceFeedBack,
)


def _extract_prices(market_data: dict[str, Any]) -> list[float]:
    prices = []
    markets = market_data.get("markets", [])
    for m in markets:
        outcomes = m.get("outcomes", [])
        if outcomes:
            for o in outcomes:
                p = o.get("price")
                if p is not None:
                    prices.append(float(p))
        else:
            p = m.get("price") or m.get("yes_price")
            if p is not None:
                prices.append(float(p))
    return prices


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def _percentile(values: list[float], p: float) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    k = (n - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, n - 1)
    return s[f] * (c - k) + s[c] * (k - f)


def _confidence_from_iqr(values: list[float], median: float) -> float:
    if len(values) < 2:
        return 0.5
    q25 = _percentile(values, 25)
    q75 = _percentile(values, 75)
    spread = max(values) - min(values)
    if spread == 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (q75 - q25) / spread))


def _agreement(values: list[float]) -> float:
    if len(values) < 2:
        return 1.0
    med = _median(values)
    avg_dev = sum(abs(v - med) for v in values) / len(values)
    if med == 0 and avg_dev == 0:
        return 1.0
    if med == 0:
        return max(0.0, min(1.0, 1.0 - avg_dev / (avg_dev + 0.5)))
    return max(0.0, min(1.0, 1.0 - avg_dev / med))


def _verification(confidence: float, n_sources: int) -> str:
    if n_sources >= 3 and confidence >= 0.7:
        return "high"
    if n_sources >= 2 and confidence >= 0.4:
        return "medium"
    return "low"


class VerifiedFeedEngine:
    """Produces verified data feeds from multiple independent sources."""

    def __init__(self, settings: Settings, provider_registry: ProviderRegistry):
        self.settings = settings
        self.providers = provider_registry

    async def produce_feed(self, feed_id: str, topic: str) -> VerifiedDataFeed:
        start = time.monotonic()
        all_providers = self.providers.list_all()
        sources: list[SourceFeedBack] = []
        all_prices: list[float] = []

        async def fetch(p):
            try:
                ts = time.monotonic()
                result = await p.get_data({"request_id": feed_id, "limit": 5})
                elapsed = (time.monotonic() - ts) * 1000
                data = result.data or {}
                prices = _extract_prices(data)
                weight = min(p.reputation.trust_score / 100.0, 1.0)
                avg = _median(prices) if prices else None
                sources.append(SourceFeedBack(
                    provider_id=p.provider_id, provider_name=p.name,
                    price=avg, confidence=_confidence_from_iqr(prices, avg) if prices else None,
                    weight=round(weight, 2), success=bool(prices),
                    error=None if prices else "no market prices found",
                ))
                all_prices.extend(prices)
            except Exception as e:
                weight = min(p.reputation.trust_score / 100.0, 1.0)
                sources.append(SourceFeedBack(
                    provider_id=p.provider_id, provider_name=p.name,
                    price=None, confidence=None, weight=round(weight, 2),
                    success=False, error=str(e)[:80],
                ))

        await asyncio.gather(*[fetch(p) for p in all_providers])
        elapsed = (time.monotonic() - start) * 1000

        agg_price = _median(all_prices) if all_prices else 0.0
        confidence = _confidence_from_iqr(all_prices, agg_price) if all_prices else 0.0
        agreement = _agreement(all_prices) if all_prices else 0.0
        verification = _verification(confidence, len([s for s in sources if s.success]))
        total_cost = sum(p.cost_hbar for p in all_providers)

        feed = VerifiedDataFeed(
            feed_id=feed_id, topic=topic,
            aggregate=VerifiedPricePoint(
                asset=topic, price=round(agg_price, 4),
                confidence=round(confidence, 4),
                sources=len([s for s in sources if s.success]),
                agreement=round(agreement, 4),
                timestamp=int(time.time()),
            ),
            sources=sources, verification=verification,
            total_cost_hbar=total_cost,
            processing_time_ms=round(elapsed, 1),
        )
        return feed
