import httpx

from providers.base_betting import BettingDataProvider
from providers.schemas_betting import (
    BettingMarket,
    BettingOutcome,
    BettingQuery,
    MarketStatus,
)


class KalshiBettingProvider(BettingDataProvider):
    provider_id = "kalshi"
    name = "Kalshi Prediction Markets"
    description = (
        "Fetches market prices, volume, and liquidity from Kalshi, "
        "a CFTC-regulated US prediction market exchange. "
        "Covers economics, climate, elections, technology, and pop culture."
    )
    cost_hbar = 0.3

    BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        params: dict = {"limit": min(query.limit, 100)}
        if query.query:
            params["tickers"] = query.query
        if query.category:
            params["series_ticker"] = query.category

        status_map = {"open": "open", "closed": "closed", "resolved": "settled"}
        if query.status and query.status in status_map:
            params["status"] = status_map[query.status]

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{self.BASE_URL}/markets", params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                raw_markets = data.get("markets", [])
                return [self._parse_market(m) for m in raw_markets]
            except Exception:
                return []

    async def get_market(self, market_id: str) -> BettingMarket | None:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{self.BASE_URL}/markets/{market_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    market = data.get("market", data)
                    return self._parse_market(market)
            except Exception:
                pass
        return None

    def _parse_market(self, data: dict) -> BettingMarket:
        yes_price = self._parse_price(data.get("yes_bid_dollars"))
        no_price = self._parse_price(data.get("no_bid_dollars"))
        volume = self._parse_count(data.get("volume_fp"))

        status_raw = data.get("status", "")
        result = data.get("result", "")
        if result in ("yes", "no"):
            status = MarketStatus.RESOLVED
        elif status_raw == "closed":
            status = MarketStatus.CLOSED
        elif status_raw == "open":
            status = MarketStatus.OPEN
        else:
            status = MarketStatus.UNKNOWN

        outcomes = []
        if yes_price is not None:
            outcomes.append(BettingOutcome(
                name="Yes", price=yes_price / 100,
                volume=volume,
            ))
        if no_price is not None:
            outcomes.append(BettingOutcome(
                name="No", price=no_price / 100,
                volume=volume,
            ))

        return BettingMarket(
            platform="kalshi",
            market_id=data.get("ticker", ""),
            title=data.get("title", "Untitled"),
            description=data.get("subtitle"),
            status=status,
            outcomes=outcomes,
            volume=float(volume) if volume else 0.0,
            liquidity=0.0,
            close_time=data.get("close_time"),
            resolution_outcome=result if result else None,
            category=data.get("series_ticker"),
            tags=[data.get("event_ticker", "")] if data.get("event_ticker") else [],
            url=f"https://kalshi.com/markets/{data.get('ticker', '')}",
        )

    def _parse_price(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value.replace("$", ""))
        except (ValueError, AttributeError):
            return None

    def _parse_count(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, AttributeError):
            return None
