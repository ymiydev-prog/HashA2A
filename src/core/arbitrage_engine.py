"""ArbitrageEngine — detects price spreads across multiple oracles."""

import time
from typing import Any

from core.oracle_hub import OracleHub, OraclePrice, ORACLE_NAMES


class ArbitrageSignal:
    def __init__(self, asset: str, prices: list[OraclePrice]):
        self.asset = asset
        self.prices = prices
        self.spread_pct = 0.0
        self.buy_from: OraclePrice | None = None
        self.sell_to: OraclePrice | None = None
        self.opportunity = "none"
        self.analysis: str | None = None
        self.timestamp = int(time.time())

    def to_dict(self) -> dict:
        return {
            "asset": self.asset,
            "timestamp": self.timestamp,
            "spread_pct": round(self.spread_pct, 4),
            "opportunity": self.opportunity,
            "buy_from": self.buy_from.to_dict() if self.buy_from else None,
            "sell_to": self.sell_to.to_dict() if self.sell_to else None,
            "prices": [p.to_dict() for p in self.prices],
            "analysis": self.analysis,
        }


class ArbitrageEngine:
    def __init__(self, oracle_hub: OracleHub):
        self.oracle_hub = oracle_hub
        self.MIN_SPREAD_PCT = 0.01

    async def scan_asset(self, asset: str) -> ArbitrageSignal:
        prices = await self.oracle_hub.get_price(asset)
        signal = ArbitrageSignal(asset, prices)
        if len(prices) < 2:
            signal.analysis = f"Only {len(prices)} oracle(s) available for {asset}"
            return signal

        prices_sorted = sorted(prices, key=lambda p: p.price)
        lowest = prices_sorted[0]
        highest = prices_sorted[-1]
        spread = highest.price - lowest.price
        mid = (highest.price + lowest.price) / 2
        spread_pct = (spread / mid) * 100 if mid > 0 else 0

        signal.spread_pct = spread_pct
        signal.buy_from = lowest
        signal.sell_to = highest

        if spread_pct >= self.MIN_SPREAD_PCT:
            signal.opportunity = "high"
        elif spread_pct >= self.MIN_SPREAD_PCT * 0.5:
            signal.opportunity = "medium"
        else:
            signal.opportunity = "low"

        confidences = [p.confidence for p in prices if p.confidence is not None]
        conf_str = f", confidence range: {min(confidences):.4f}-{max(confidences):.4f}" if confidences else ""
        signal.analysis = (
            f"{asset}: spread {spread_pct:.3f}% across {len(prices)} oracles. "
            f"Buy at ${lowest.price:.2f} ({lowest.source_name}), "
            f"sell at ${highest.price:.2f} ({highest.source_name}). "
            f"Opportunity: {signal.opportunity}{conf_str}."
        )
        return signal

    async def scan_all(self) -> list[ArbitrageSignal]:
        all_prices = await self.oracle_hub.get_all_prices()
        signals = []
        for asset in all_prices:
            signal = await self.scan_asset(asset)
            signals.append(signal)
        signals.sort(key=lambda s: s.spread_pct, reverse=True)
        return signals
