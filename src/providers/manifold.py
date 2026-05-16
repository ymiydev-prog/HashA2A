import httpx

from providers.base_betting import BettingDataProvider
from providers.schemas_betting import BettingMarket, BettingOutcome, BettingQuery, MarketStatus


class ManifoldMarketsProvider(BettingDataProvider):
    provider_id = "manifold"
    name = "Manifold Markets"
    description = (
        "Fetches prediction market data from Manifold Markets, a community-driven prediction platform. "
        "Covers politics, science, technology, crypto, and culture with play-money trading."
    )
    cost_hbar = 0.3

    API_URL = "https://api.manifold.markets/v0/markets"

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        params: dict = {
            "limit": min(query.limit * 3, 100),
        }
        if query.query:
            params["term"] = query.query

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(self.API_URL, params=params)
                if resp.status_code != 200:
                    return []
                raw = resp.json()
                items = raw if isinstance(raw, list) else raw.get("markets", [])

                results = []
                for m in items:
                    parsed = self._parse_market(m)
                    if parsed.outcomes:
                        results.append(parsed)
                    if len(results) >= query.limit:
                        break

                return results
            except Exception:
                return []

    async def get_market(self, market_id: str) -> BettingMarket | None:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{self.API_URL}?id={market_id}")
                if resp.status_code != 200:
                    return None
                raw = resp.json()
                items = raw if isinstance(raw, list) else raw.get("markets", [])
                if items:
                    return self._parse_market(items[0])
                return None
            except Exception:
                return None

    def _parse_market(self, data: dict) -> BettingMarket:
        prob = data.get("probability")
        volume = data.get("volume", 0) or 0
        liquidity = data.get("liquidity", 0) or 0

        outcomes = []
        if data.get("outcomeType") == "BINARY":
            yes_price = prob if prob is not None else None
            no_price = (1.0 - prob) if prob is not None else None
            if yes_price is not None:
                outcomes.append(BettingOutcome(
                    name="Yes",
                    price=yes_price,
                    volume=float(volume),
                ))
            if no_price is not None:
                outcomes.append(BettingOutcome(
                    name="No",
                    price=no_price,
                    volume=float(volume),
                ))
        else:
            if prob is not None:
                outcomes.append(BettingOutcome(
                    name=data.get("question", "Unknown"),
                    price=prob,
                    volume=float(volume),
                ))

        is_closed = data.get("closed", False)
        is_resolved = data.get("resolved", False)
        if is_resolved:
            status = MarketStatus.RESOLVED
        elif is_closed:
            status = MarketStatus.CLOSED
        else:
            status = MarketStatus.OPEN

        close_time = data.get("closeTime")
        if close_time:
            if isinstance(close_time, (int, float)):
                from datetime import datetime
                close_time = datetime.utcfromtimestamp(close_time / 1000).isoformat() if close_time > 1e9 else datetime.utcfromtimestamp(close_time).isoformat()

        resolution = data.get("resolution")
        resolution_outcome = None
        if resolution == "YES":
            resolution_outcome = "Yes"
        elif resolution == "NO":
            resolution_outcome = "No"
        elif resolution:
            resolution_outcome = str(resolution)

        return BettingMarket(
            platform="manifold",
            market_id=data.get("id", ""),
            title=data.get("question", "Untitled"),
            description=data.get("description", {}).get("content") if isinstance(data.get("description"), dict) else data.get("description"),
            status=status,
            outcomes=outcomes,
            volume=float(volume),
            liquidity=float(liquidity),
            close_time=close_time,
            resolution_outcome=resolution_outcome,
            category=data.get("groupSlug"),
            tags=data.get("tags", []),
            url=f"https://manifold.markets/{data.get('creatorUsername', '')}/{data.get('slug', '')}" if data.get("slug") else None,
        )
