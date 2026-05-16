"""Content scheduler for X/Twitter — posts varied content on schedule."""

import json
import os
import random
import time
from typing import Any

HAS_TWEEPY = True


def _cache_path() -> str:
    d = os.environ.get("HASHA2A_CACHE_DIR", os.path.expanduser("~/.hasha2a"))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "content_schedule.json")


def _load_tracker() -> dict:
    p = _cache_path()
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_tracker(t: dict) -> None:
    p = _cache_path()
    try:
        with open(p, "w") as f:
            json.dump(t, f)
    except Exception:
        pass


class ContentScheduler:
    """Follows CONTENT_PLAN.md schedule automatically — posts daily, varied content."""

    PRICE_TEMPLATES = [
        "🔮 {asset}: ${price:,.2f}\n━━━━━━━━━━━━━━━━━\n{rows}━━━━━━━━━━━━━━━━━\nSpread: {spread}%\nOracles: {count}",
        "📊 {asset} Multi-Oracle\n━━━━━━━━━━━━━━━━━\nMedian: ${price:,.2f}\nConfidence: {confidence}\nSpread: {spread}%\n━━━━━━━━━━━━━━━━━\nData via HashA2A OracleHub",
    ]
    SHOWDOWN_TEMPLATES = [
        "🔮 Oracle Showdown — {asset}\n{rows}All {count} verified independently.\nhasha2a.dev",
    ]
    ARBITRAGE_TEMPLATES = [
        "📊 Arbitrage: {asset}\n━━━━━━━━━━━━━━━━━━━━\nBuy: {buy_from} (${buy_price:,.2f})\nSell: {sell_to} (${sell_price:,.2f})\n━━━━━━━━━━━━━━━━━━━━\nSpread: {spread}%\nVentana: <30s",
        "📈 Top arbitrage del día\n━━━━━━━━━━━━━━━━━━━━\n{top}\n━━━━━━━━━━━━━━━━━━━━\nDetected by HashA2A Arbitrage Engine",
    ]
    TUTORIAL_TEMPLATES = [
        "🧵 How your AI agent gets verified prices in 3 steps:\n\n1. Connect to MCP:\n{{\n  \"mcpServers\": {{\n    \"hasha2a\": {{\"url\": \"localhost:8080/mcp\"}}\n  }}\n}}\n\n2. Call get_price(\"BTC/USD\")\n3. Get verified multi-oracle price\n\nNo API keys. No subscription.",
        "🔌 HashA2A is now Google A2A Protocol compatible\n\nAny A2A agent can:\n• Send tasks via JSON-RPC 2.0\n• Receive SSE streaming\n• Pay with USDC (x402) or HBAR (HIP-991)\n• Pass context between sessions\n\nSpec: /.well-known/agent.json",
        "🚀 New: Arbitrage Scanner\n\nHashA2A detects price differences BETWEEN oracles.\nIf Pyth says $50,100 and CoinGecko says $50,050...\nwe tell you where to buy/sell.\n\nReal-time. No polling. Pay-per-query.",
        "🧠 What is OracleHub?\n\nHashA2A queries 3 sources SIMULTANEOUSLY:\n• Pyth (first-party exchanges, 400ms)\n• CoinGecko (200+ exchanges)\n• DeFiLlama/Chainlink (11 nodes)\n\n→ Median + IQR + confidence score\n\nVerified data, not a random number.",
    ]
    WEEKLY_TEMPLATES = [
        "📆 HashA2A Weekly — Week {week}\n━━━━━━━━━━━━━━━━━\n{stats}\n━━━━━━━━━━━━━━━━━\nRunning 24/7 on Hedera testnet.",
    ]

    def __init__(self, api_key: str | None = None, api_secret: str | None = None,
                 access_token: str | None = None, access_secret: str | None = None,
                 enabled: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.enabled = enabled and bool(api_key) and bool(access_token)
        self._last_tweet: float = 0
        self._min_interval: float = 7200
        self._client: Any = None
        self._tracker = _load_tracker()
        if "day_count" not in self._tracker:
            self._tracker = {"day_count": 0, "week_count": 1, "posts": {}}
        self._tracker["day_count"] = self._tracker.get("day_count", 0) + 1
        if self._tracker["day_count"] >= 7:
            self._tracker["day_count"] = 0
            self._tracker["week_count"] = self._tracker.get("week_count", 1) + 1

    def _save(self):
        _save_tracker(self._tracker)

    def _get_client(self):
        if self._client is None:
            import tweepy
            self._client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
            )
        return self._client

    async def post_tweet(self, text: str) -> bool:
        if not self.enabled:
            return False
        if len(text) > 280:
            text = text[:277] + "..."
        now = time.time()
        if now - self._last_tweet < self._min_interval:
            return False
        self._last_tweet = now
        try:
            c = self._get_client()
            import asyncio
            r = await asyncio.to_thread(c.create_tweet, text=text)
            return r is not None and r.data is not None
        except Exception:
            return False

    def _fmt(self, tpl: str, **kw) -> str:
        return tpl.format(**kw)

    def _pick(self, templates: list[str]) -> str:
        return random.choice(templates)

    async def post_price(self, asset: str, prices: list[dict]) -> bool:
        if not prices:
            return False
        vals = [p["price"] for p in prices]
        med = sum(vals) / len(vals)
        spread = (max(vals) - min(vals)) / med * 100 if med else 0
        rows = "\n".join(f"{p['source_name']:12s} ${p['price']:>8,.2f}" for p in prices)
        conf = "HIGH" if spread < 0.05 else "MEDIUM" if spread < 0.2 else "LOW"
        tpl = self._pick(self.PRICE_TEMPLATES + self.SHOWDOWN_TEMPLATES if "Showdown" in self._tracker.get("last_type", "") else self.PRICE_TEMPLATES)
        text = self._fmt(tpl, asset=asset, price=med, rows=rows, spread=f"{spread:.3f}", count=len(prices), confidence=conf)
        ok = await self.post_tweet(text)
        if ok:
            self._tracker["last_type"] = "price"
            self._save()
        return ok

    async def post_arbitrage(self, signals: list[dict]) -> bool:
        if not signals:
            return False
        best = signals[0]
        if best.get("spread_pct", 0) < 0.01:
            return False
        buy = best.get("buy_from", {})
        sell = best.get("sell_to", {})
        text = self._fmt(
            self._pick(self.ARBITRAGE_TEMPLATES),
            asset=best.get("asset", "?"),
            buy_from=buy.get("source_name", "?"),
            buy_price=buy.get("price", 0),
            sell_to=sell.get("source_name", "?"),
            sell_price=sell.get("price", 0),
            spread=f"{best['spread_pct']:.3f}",
            top="\n".join(
                f"{i+1}. {s['asset']} → {s['spread_pct']:.3f}%"
                for i, s in enumerate(signals[:3])
            ),
        )
        ok = await self.post_tweet(text)
        if ok:
            self._tracker["last_type"] = "arbitrage"
            self._save()
        return ok

    async def post_tutorial(self) -> bool:
        tpl = random.choice(self.TUTORIAL_TEMPLATES)
        ok = await self.post_tweet(tpl)
        if ok:
            self._tracker["last_type"] = "tutorial"
            self._save()
        return ok

    async def post_weekly(self, total_tasks: int, providers: int, oracles: int) -> bool:
        stats = f"Tasks: {total_tasks}\nProviders: {providers}\nOracles: {oracles}\nVersion: 0.2.0"
        text = self._fmt(
            self.WEEKLY_TEMPLATES[0],
            week=self._tracker.get("week_count", 1),
            stats=stats,
        )
        ok = await self.post_tweet(text)
        if ok:
            self._tracker["last_type"] = "weekly"
            self._save()
        return ok

    async def run_scheduled(self, total_tasks: int, providers: int, oracles: int) -> bool:
        """Run based on content plan schedule (called from periodic broadcast)."""
        now = time.time()
        lt = time.localtime(now)
        hour = lt.tm_hour
        wday = lt.tm_wday  # 0=Mon

        day_type = self._tracker.get("last_type", "")
        day_count = self._tracker.get("day_count", 0)

        if hour < 8 or hour > 22:
            return False

        morning = 8 <= hour <= 10
        afternoon = 14 <= hour <= 16
        is_saturday = wday == 5
        is_sunday = wday == 6

        # Morning slot: price feeds
        if morning:
            from core.oracle_hub import OracleHub
            hub = OracleHub()
            try:
                import asyncio
                for asset in ["BTC/USD", "ETH/USD"]:
                    prices = await asyncio.wait_for(hub.get_price(asset), timeout=5)
                    if prices and day_type != "price":
                        await self.post_price(asset, [p.to_dict() for p in prices])
                        break
                if is_saturday and day_type != "showdown":
                    prices = await asyncio.wait_for(hub.get_price("BTC/USD"), timeout=5)
                    if prices:
                        tpl = self.SHOWDOWN_TEMPLATES[0]
                        rows = "\n".join(
                            f"{p.source_name:15s} ${p.price:>8,.2f}"
                            for p in prices
                        )
                        text = self._fmt(tpl, asset="BTC/USD", rows=rows, count=len(prices))
                        ok = await self.post_tweet(text)
                        if ok:
                            self._tracker["last_type"] = "showdown"
                            self._save()
                if is_sunday and day_type != "weekly":
                    await self.post_weekly(total_tasks, providers, oracles)
            except Exception:
                pass
            await hub.close()
            return True

        # Afternoon slot: arbitrage (Mon/Wed/Fri) or tutorial (Tue/Thu)
        if afternoon:
            if wday in (0, 2, 4) and day_type != "arbitrage":
                from core.oracle_hub import OracleHub
                from core.arbitrage_engine import ArbitrageEngine
                hub = OracleHub()
                try:
                    import asyncio
                    engine = ArbitrageEngine(hub)
                    signals = await asyncio.wait_for(engine.scan_all(), timeout=8)
                    if signals:
                        await self.post_arbitrage([s.to_dict() for s in signals[:3]])
                except Exception:
                    pass
                await hub.close()
                return True
            if wday in (1, 3) and day_type != "tutorial":
                await self.post_tutorial()
                return True

        return False
