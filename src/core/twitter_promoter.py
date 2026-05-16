"""Auto-promotion service for X/Twitter — tweets price data, arbitrage, and stats."""

import asyncio
import time
from typing import Any

import httpx


class TwitterPromoter:
    """Posts automated promotional tweets about HashA2A activity."""

    def __init__(self, bearer_token: str | None, api_key: str | None = None,
                 api_secret: str | None = None, enabled: bool = False):
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.enabled = enabled and bool(bearer_token)
        self._last_tweet: float = 0
        self._min_interval: float = 3600  # 1 hour minimum between auto-tweets
        self._http: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10)
        return self._http

    async def close(self):
        if self._http:
            await self._http.aclose()
            self._http = None

    async def post_tweet(self, text: str) -> bool:
        if not self.enabled or not self.bearer_token:
            return False
        if len(text) > 280:
            text = text[:277] + "..."

        now = time.time()
        if now - self._last_tweet < self._min_interval:
            return False
        self._last_tweet = now

        try:
            c = await self._client()
            resp = await c.post(
                "https://api.twitter.com/2/tweets",
                json={"text": text},
                headers={"Authorization": f"Bearer {self.bearer_token}"},
            )
            return resp.status_code in (200, 201)
        except Exception:
            return False

    async def tweet_price_feed(self, asset: str, prices: list[dict]) -> bool:
        if not prices:
            return False
        p = prices[0]
        text = (
            f"🔮 ${p['price']:,.2f} — {asset}\n"
            f"Verified by {len(prices)} oracles"
        )
        if len(prices) >= 2:
            vals = [p["price"] for p in prices]
            spread = (max(vals) - min(vals)) / (sum(vals) / len(vals)) * 100
            text += f" | Spread: {spread:.3f}%"
        return await self.post_tweet(text)

    async def tweet_arbitrage(self, asset: str, spread_pct: float,
                              buy_from: str, sell_to: str) -> bool:
        text = (
            f"📊 Arbitrage: {asset}\n"
            f"Spread: {spread_pct:.3f}%\n"
            f"Buy: {buy_from} → Sell: {sell_to}\n"
            f"hasha2a.io"
        )
        return await self.post_tweet(text[:280])

    async def tweet_stats(self, total_tasks: int, providers: int,
                          oracles: int, version: str) -> bool:
        text = (
            f"🤖 HashA2A v{version}\n"
            f"📦 {providers} providers · {oracles} oracles\n"
            f"✅ {total_tasks} tasks processed\n"
            f"Agent-to-Agent Intelligence Layer"
        )
        return await self.post_tweet(text[:280])

    async def tweet_feature(self, feature: str, description: str) -> bool:
        text = f"🚀 {feature}\n{description[:200]}"
        return await self.post_tweet(text[:280])
