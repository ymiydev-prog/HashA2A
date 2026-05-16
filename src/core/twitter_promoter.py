"""Auto-promotion for X/Twitter — tweets price data, arbitrage, and stats."""

import time
from typing import Any

HAS_TWEEPY = True


class TwitterPromoter:
    """Posts automated promotional tweets about HashA2A activity."""

    def __init__(self, bearer_token: str | None = None, api_key: str | None = None,
                 api_secret: str | None = None, access_token: str | None = None,
                 access_secret: str | None = None, enabled: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.enabled = enabled and bool(api_key) and bool(access_token)
        self._last_tweet: float = 0
        self._min_interval: float = 3600
        self._client: Any = None

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
            client = self._get_client()
            if client is None:
                return False
            import asyncio
            result = await asyncio.to_thread(client.create_tweet, text=text)
            return result is not None and result.data is not None
        except Exception:
            return False

    async def tweet_price_feed(self, asset: str, prices: list[dict]) -> bool:
        if not prices:
            return False
        vals = [p["price"] for p in prices]
        spread = (max(vals) - min(vals)) / (sum(vals) / len(vals)) * 100
        text = (
            f"🔮 ${prices[0]['price']:,.2f} — {asset}\n"
            f"Verified by {len(prices)} oracles | Spread: {spread:.3f}%\n"
            f"hasha2a.dev"
        )
        return await self.post_tweet(text)

    async def tweet_arbitrage(self, asset: str, spread_pct: float,
                              buy_from: str, sell_to: str) -> bool:
        text = (
            f"📊 Arbitrage: {asset}\n"
            f"Spread: {spread_pct:.3f}%\n"
            f"Buy: {buy_from} → Sell: {sell_to}\n"
            f"hasha2a.dev"
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
