import asyncio
import httpx

from providers.base_betting import BettingDataProvider
from providers.schemas_betting import BettingMarket, BettingOutcome, BettingQuery, MarketStatus


class HyperliquidProvider(BettingDataProvider):
    provider_id = "hyperliquid"
    name = "Hyperliquid HIP-4"
    description = (
        "Fetches on-chain binary outcome markets from Hyperliquid's HIP-4 protocol. "
        "Fully-collateralized YES/NO contracts that settle on HyperCore's CLOB against "
        "authorized oracles. Covers crypto price targets, with categorical multi-outcome "
        "markets on testnet. Combined ~$7B daily volume across the exchange."
    )
    cost_hbar = 0.3

    INFO_URL = "https://api.hyperliquid.xyz/info"

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        outcomes = []
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(self.INFO_URL, json={"type": "outcomeMeta"})
                if resp.status_code == 200:
                    data = resp.json()
                    outcomes = data.get("outcomes", [])
            except Exception:
                pass

        results = []
        for raw in outcomes:
            outcome_id = raw.get("outcome")
            if outcome_id is None:
                continue

            market = self._parse_outcome(raw)
            if query.query and query.query.lower() not in market.title.lower():
                continue

            results.append(market)
            if len(results) >= query.limit:
                break

        if results:
            async with httpx.AsyncClient(timeout=15) as client:
                await self._hydrate_prices(client, results)

        return results

    async def get_market(self, market_id: str) -> BettingMarket | None:
        outcomes = []
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(self.INFO_URL, json={"type": "outcomeMeta"})
                if resp.status_code == 200:
                    data = resp.json()
                    outcomes = data.get("outcomes", [])
            except Exception:
                pass

        for raw in outcomes:
            if str(raw.get("outcome")) == market_id:
                market = self._parse_outcome(raw)
                async with httpx.AsyncClient(timeout=15) as client:
                    await self._hydrate_prices(client, [market])
                return market
        return None

    def _parse_outcome(self, data: dict) -> BettingMarket:
        outcome_id = data.get("outcome", 0)
        name = data.get("name", "Unknown")
        description_raw = data.get("description", "")
        side_specs = data.get("sideSpecs", [])

        desc = self._parse_description(description_raw)

        title = desc.get("underlying", name)
        if desc.get("targetPrice"):
            title = f"{title} {'>' if desc.get('class') == 'priceBinary' else ''}${desc['targetPrice']}"
        if desc.get("expiry"):
            title = f"{title} by {desc['expiry']}"
        if desc.get("period"):
            title = f"{title} ({desc['period']})"

        is_settled = False
        expiry_str = desc.get("expiry", "")
        if expiry_str:
            try:
                from datetime import datetime
                expiry = datetime.strptime(expiry_str, "%Y%m%d-%H%M")
                if expiry < datetime.utcnow():
                    is_settled = True
            except ValueError:
                pass

        status = MarketStatus.RESOLVED if is_settled else MarketStatus.OPEN

        outcomes = []
        has_yes = any(s.get("name", "").lower() in ("yes", "long") for s in side_specs)
        has_no = any(s.get("name", "").lower() in ("no", "short") for s in side_specs)

        if has_yes:
            outcomes.append(BettingOutcome(name="Yes", price=None, volume=None))
        if has_no:
            outcomes.append(BettingOutcome(name="No", price=None, volume=None))
        if not outcomes:
            for s in side_specs:
                outcomes.append(BettingOutcome(name=s.get("name", "Side"), price=None, volume=None))

        market_class = desc.get("class", "")
        tags = [market_class] if market_class else []
        if desc.get("underlying"):
            tags.append(desc["underlying"])
        if desc.get("period"):
            tags.append(desc["period"])

        return BettingMarket(
            platform="hyperliquid",
            market_id=str(outcome_id),
            title=title,
            description=description_raw or None,
            status=status,
            outcomes=outcomes,
            volume=0.0,
            liquidity=0.0,
            close_time=desc.get("expiry"),
            resolution_outcome=None,
            category=desc.get("class"),
            tags=tags,
            url=f"https://app.hyperliquid.xyz/trade/#{outcome_id * 10}" if outcome_id else None,
        )

    async def _hydrate_prices(
        self, client: httpx.AsyncClient, markets: list[BettingMarket]
    ):
        price_tasks = {}
        for m in markets:
            outcome_id = int(m.market_id)
            yes_coin = f"#{outcome_id * 10}"
            price_tasks[(m.market_id, "yes")] = self._fetch_side_price(client, yes_coin)
            if any(o.name.lower() == "no" for o in m.outcomes):
                no_coin = f"#{outcome_id * 10 + 1}"
                price_tasks[(m.market_id, "no")] = self._fetch_side_price(client, no_coin)

        results = await asyncio.gather(
            *price_tasks.values(), return_exceptions=True
        )
        result_map = dict(zip(price_tasks.keys(), results))

        for m in markets:
            yes_price = result_map.get((m.market_id, "yes"))
            no_price = result_map.get((m.market_id, "no"))
            if isinstance(yes_price, Exception):
                yes_price = None
            if isinstance(no_price, Exception):
                no_price = None

            for outcome in m.outcomes:
                if outcome.name.lower() == "yes" and yes_price is not None:
                    outcome.price = yes_price
                elif outcome.name.lower() == "no":
                    if no_price is not None:
                        outcome.price = no_price
                    elif yes_price is not None:
                        outcome.price = round(1.0 - yes_price, 4)

    async def _fetch_side_price(
        self, client: httpx.AsyncClient, coin: str
    ) -> float | None:
        try:
            resp = await client.post(
                self.INFO_URL, json={"type": "l2Book", "coin": coin}
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            levels = data.get("levels", [])
            if not levels:
                return None

            all_prices = []
            for side_levels in levels:
                if not isinstance(side_levels, list):
                    continue
                for entry in side_levels:
                    if not isinstance(entry, dict):
                        continue
                    try:
                        px = float(entry.get("px", 0))
                        sz = float(entry.get("sz", 0))
                        if px > 0 and sz > 0:
                            all_prices.append(px)
                    except (ValueError, TypeError):
                        continue

            if not all_prices:
                return None

            all_prices.sort()
            n = len(all_prices)
            mid = all_prices[n // 2] if n > 1 else all_prices[0]
            return round(mid, 4)
        except Exception:
            return None

    @staticmethod
    def _parse_description(raw: str) -> dict:
        result = {}
        if not raw:
            return result
        parts = raw.split("|")
        for part in parts:
            kv = part.split(":", 1)
            if len(kv) == 2:
                result[kv[0].strip()] = kv[1].strip()
            elif part.strip():
                result["raw"] = part.strip()
        return result
