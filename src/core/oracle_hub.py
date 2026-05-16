"""OracleHub — connects to Chainlink (via DeFiLlama), Pyth Hermes, and CoinGecko."""

import asyncio
import time
from typing import Any

import httpx


PYTH_FEEDS = {
    "BTC/USD": "e62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    "ETH/USD": "ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
    "SOL/USD": "ef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
    "USD/JPY": "ef2c98c804ba503c6a707e38be4dfbb16683775f195b091252bf24693042fd52",
    "XAU/USD": "765d2ba906dbc32ca17cc11f5310a89e9ee1f6420508c63861f2f8ba4ee34bb2",
    "XAG/USD": "f2fb02c32b055c805e7238d628e5e9dadef274376114eb1f012337cabe93871e",
}

COINGECKO_IDS = {
    "BTC/USD": "bitcoin",
    "ETH/USD": "ethereum",
    "SOL/USD": "solana",
    "BNB/USD": "binancecoin",
    "XRP/USD": "ripple",
    "ADA/USD": "cardano",
    "DOGE/USD": "dogecoin",
    "AVAX/USD": "avalanche-2",
    "DOT/USD": "polkadot",
    "LINK/USD": "chainlink",
    "UNI/USD": "uniswap",
    "AAVE/USD": "aave",
    "ATOM/USD": "cosmos",
    "ARB/USD": "arbitrum",
    "APT/USD": "aptos",
    "OP/USD": "optimism",
    "SUI/USD": "sui",
}

ORACLE_NAMES = {
    "pyth": "Pyth Network",
    "coingecko": "CoinGecko",
    "defillama": "DeFiLlama (Chainlink)",
}


class OraclePrice:
    def __init__(self, source: str, asset: str, price: float, confidence: float | None, timestamp: int):
        self.source = source
        self.source_name = ORACLE_NAMES.get(source, source)
        self.asset = asset
        self.price = price
        self.confidence = confidence
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "source_name": self.source_name,
            "asset": self.asset,
            "price": self.price,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class OracleHub:
    """Fetches prices from multiple free oracle sources simultaneously."""

    def __init__(self, cache_ttl: int = 15):
        self._http: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[float, list[OraclePrice]]] = {}
        self._cache_ttl = cache_ttl

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10)
        return self._http

    async def close(self):
        if self._http:
            await self._http.aclose()
            self._http = None

    async def get_price(self, asset: str) -> list[OraclePrice]:
        now = time.time()
        cached = self._cache.get(asset)
        if cached and (now - cached[0]) < self._cache_ttl:
            return cached[1]

        results: list[OraclePrice] = []
        tasks = []
        if asset in PYTH_FEEDS:
            tasks.append(self._fetch_pyth(asset))
        if asset in COINGECKO_IDS:
            tasks.append(self._fetch_coingecko(asset))
        tasks.append(self._fetch_defillama(asset))

        done = await asyncio.gather(*tasks, return_exceptions=True)
        for r in done:
            if isinstance(r, OraclePrice):
                results.append(r)

        if results:
            self._cache[asset] = (now, results)
        return results

    async def get_all_prices(self) -> dict[str, list[OraclePrice]]:
        assets = list(set(list(PYTH_FEEDS.keys()) + list(COINGECKO_IDS.keys())))
        results = {}
        tasks = {a: self.get_price(a) for a in assets}
        for asset, task in tasks.items():
            try:
                prices = await task
                if prices:
                    results[asset] = prices
            except Exception:
                pass
        return results

    async def invalidate_cache(self, asset: str | None = None):
        if asset:
            self._cache.pop(asset, None)
        else:
            self._cache.clear()

    async def _fetch_pyth(self, asset: str) -> OraclePrice | None:
        feed_id = PYTH_FEEDS.get(asset)
        if not feed_id:
            return None
        try:
            c = await self._client()
            resp = await c.get(
                f"https://hermes.pyth.network/v2/updates/price/latest",
                params={"ids[]": feed_id},
            )
            data = resp.json()
            parsed = data.get("parsed", [])
            if not parsed:
                return None
            p = parsed[0]["price"]
            price = float(p["price"]) * (10 ** p["expo"])
            conf = float(p["conf"]) * (10 ** p["expo"]) if p.get("conf") else None
            return OraclePrice("pyth", asset, price, conf, p["publish_time"])
        except Exception:
            return None

    async def _fetch_coingecko(self, asset: str) -> OraclePrice | None:
        cg_id = COINGECKO_IDS.get(asset)
        if not cg_id:
            return None
        try:
            c = await self._client()
            resp = await c.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": cg_id, "vs_currencies": "usd"},
            )
            data = resp.json()
            price = data.get(cg_id, {}).get("usd")
            if price is None:
                return None
            return OraclePrice("coingecko", asset, float(price), None, int(time.time()))
        except Exception:
            return None

    async def _fetch_defillama(self, asset: str) -> OraclePrice | None:
        mapping = {"BTC/USD": "bitcoin", "ETH/USD": "ethereum", "SOL/USD": "solana"}
        llama_id = mapping.get(asset)
        if not llama_id:
            return None
        try:
            c = await self._client()
            resp = await c.get(f"https://coins.llama.fi/prices/current/coingecko:{llama_id}")
            data = resp.json()
            coin = data.get("coins", {}).get(f"coingecko:{llama_id}")
            if not coin:
                return None
            return OraclePrice("defillama", asset, float(coin["price"]), None, coin.get("timestamp", 0))
        except Exception:
            return None
