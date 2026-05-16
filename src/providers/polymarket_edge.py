import json
import httpx

from providers.base_betting import BettingDataProvider
from providers.schemas_betting import BettingMarket, BettingOutcome, BettingQuery, MarketStatus


class PolymarketEdgeProvider(BettingDataProvider):
    provider_id = "polymarket"
    name = "Polymarket Edge"
    description = (
        "Fetches prediction market odds, volume, liquidity, and trends "
        "from Polymarket, the world's largest crypto prediction market. "
        "Covers crypto, politics, sports, science, and pop culture."
    )
    cost_hbar = 0.5

    GAMMA_API = "https://gamma-api.polymarket.com"

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
        outcomes_raw = data.get("outcomes", [])
        if isinstance(outcomes_raw, str):
            try:
                outcomes_raw = json.loads(outcomes_raw)
            except (json.JSONDecodeError, TypeError):
                outcomes_raw = []

        prices_raw = data.get("outcomePrices", [])
        if isinstance(prices_raw, str):
            try:
                prices_raw = json.loads(prices_raw)
            except (json.JSONDecodeError, TypeError):
                prices_raw = []

        outcomes = []
        for i, name in enumerate(outcomes_raw):
            price = None
            if i < len(prices_raw):
                try:
                    price = float(prices_raw[i])
                except (ValueError, TypeError):
                    pass
            outcomes.append(BettingOutcome(
                name=name,
                price=price,
                volume=None,
            ))

        is_closed = data.get("closed", False)
        resolved = data.get("resolved", False)
        if resolved:
            status = MarketStatus.RESOLVED
        elif is_closed:
            status = MarketStatus.CLOSED
        else:
            status = MarketStatus.OPEN

        return BettingMarket(
            platform="polymarket",
            market_id=str(data.get("id", "")),
            title=data.get("question", "Untitled"),
            description=data.get("description"),
            status=status,
            outcomes=outcomes,
            volume=float(data.get("volume", 0) or 0),
            liquidity=float(data.get("liquidity", 0) or 0),
            close_time=data.get("endDate"),
            resolution_outcome=None,
            category=data.get("category"),
            tags=data.get("tags", []),
            url=f"https://polymarket.com/event/{data.get('slug', '')}" if data.get("slug") else None,
        )
