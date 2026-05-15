import httpx

from providers.base_betting import BettingDataProvider
from providers.schemas_betting import BettingMarket, BettingOutcome, BettingQuery, MarketStatus


class PredictItProvider(BettingDataProvider):
    provider_id = "predictit"
    name = "PredictIt Markets"
    description = (
        "Fetches prediction market data from PredictIt, a popular political and event prediction platform. "
        "Covers US politics, elections, government, and current events with real-money trading."
    )
    cost_hbar = 0.4

    API_URL = "https://www.predictit.org/api/marketdata/all"

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(self.API_URL)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                markets_raw = data.get("markets", data.get("Markets", []))

                results = []
                for m in markets_raw:
                    if query.query and query.query.lower() not in m.get("name", m.get("Name", "")).lower():
                        continue
                    results.append(self._parse_market(m))
                    if len(results) >= query.limit:
                        break

                return results
            except Exception:
                return []

    async def get_market(self, market_id: str) -> BettingMarket | None:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(self.API_URL)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                markets_raw = data.get("markets", data.get("Markets", []))
                for m in markets_raw:
                    if str(m.get("id", m.get("ID", ""))) == market_id:
                        return self._parse_market(m)
                return None
            except Exception:
                return None

    def _parse_market(self, data: dict) -> BettingMarket:
        contracts_raw = data.get("contracts", data.get("Outcomes", [])) or []
        outcomes = []
        for c in contracts_raw:
            name = c.get("name", c.get("Name", "Unknown"))
            last_trade = c.get("lastTradePrice")
            best_buy_yes = c.get("bestBuyYesCost")
            best_sell_yes = c.get("bestSellYesCost")

            price = None
            if last_trade is not None:
                price = float(last_trade) / 100
            elif best_buy_yes is not None:
                price = float(best_buy_yes) / 100
            elif best_sell_yes is not None:
                price = float(best_sell_yes) / 100

            volume = None
            if c.get("totalTradedVolume"):
                volume = float(c["totalTradedVolume"])

            outcomes.append(BettingOutcome(
                name=name,
                price=price,
                volume=volume,
            ))

        status_raw = data.get("status", data.get("Status", "")).lower()
        if status_raw == "resolved":
            status = MarketStatus.RESOLVED
        elif status_raw == "closed":
            status = MarketStatus.CLOSED
        elif status_raw == "open":
            status = MarketStatus.OPEN
        else:
            status = MarketStatus.UNKNOWN

        return BettingMarket(
            platform="predictit",
            market_id=str(data.get("id", data.get("ID", ""))),
            title=data.get("name", data.get("Name", "Untitled")),
            description=data.get("shortName", data.get("Subtitle")),
            status=status,
            outcomes=outcomes,
            volume=0.0,
            liquidity=0.0,
            close_time=data.get("dateEnd", data.get("CloseDate")),
            resolution_outcome=None,
            category=None,
            tags=[],
            url=data.get("url") or (f"https://www.predictit.org/markets/detail/{data.get('id', data.get('ID', ''))}" if data.get("id") or data.get("ID") else None),
        )
