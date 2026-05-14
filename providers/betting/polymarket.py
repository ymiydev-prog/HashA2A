import httpx

from providers.betting.base import BettingDataProvider
from providers.betting.schemas import (
    BettingMarket,
    BettingOutcome,
    BettingQuery,
    MarketStatus,
)


class PolymarketBettingProvider(BettingDataProvider):
    provider_id = "polymarket"
    name = "Polymarket Prediction Markets"
    description = (
        "Fetches prediction market odds, volume, liquidity, and trends "
        "from Polymarket, the world's largest crypto prediction market. "
        "Covers crypto, politics, sports, science, and pop culture."
    )
    cost_hbar = 0.5

    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        params: dict = {"limit": query.limit, "closed": False}
        if query.query:
            params["query"] = query.query
        if query.category:
            params["category"] = query.category

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{self.GAMMA_API}/markets", params=params)
                if resp.status_code != 200:
                    return []
                raw = resp.json()
                items = raw if isinstance(raw, list) else raw.get("data", [])
                return [self._parse_market(m) for m in items]
            except Exception:
                return []

    async def get_market(self, market_id: str) -> BettingMarket | None:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{self.GAMMA_API}/markets/{market_id}")
                if resp.status_code == 200:
                    return self._parse_market(resp.json())
            except Exception:
                pass
        return None

    def _parse_market(self, data: dict) -> BettingMarket:
        outcomes_raw = data.get("outcomes", []) or []
        outcomes = []
        for o in outcomes_raw:
            name = o.get("name", "Unknown")
            price = o.get("price")
            if price is not None:
                price = float(price)
            token_id = o.get("token_id")
            outcome_volume = o.get("volume")
            outcomes.append(
                BettingOutcome(
                    name=name,
                    price=price,
                    volume=float(outcome_volume) if outcome_volume else None,
                    token_id=token_id,
                )
            )

        is_closed = data.get("closed", False)
        is_resolved = data.get("resolved", False)
        if is_resolved:
            status = MarketStatus.RESOLVED
        elif is_closed:
            status = MarketStatus.CLOSED
        else:
            status = MarketStatus.OPEN

        return BettingMarket(
            platform="polymarket",
            market_id=data.get("id", ""),
            title=data.get("title", "Untitled"),
            description=data.get("description"),
            status=status,
            outcomes=outcomes,
            volume=float(data.get("volume", 0) or 0),
            liquidity=float(data.get("liquidity", 0) or 0),
            close_time=data.get("close_time"),
            resolution_outcome=data.get("outcome"),
            category=data.get("category"),
            tags=data.get("tags", []),
            url=f"https://polymarket.com/event/{data.get('slug', '')}" if data.get("slug") else None,
        )
