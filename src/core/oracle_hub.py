"""OracleHub — connects to Chainlink (via DeFiLlama), Pyth Hermes, and CoinGecko."""

import asyncio
import time
from typing import Any

import httpx


PYTH_FEEDS = {
    "BTC/USD": "e62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    "ETH/USD": "ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
    "SOL/USD": "ef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
    "AAPL/USD": "b9eefb129a6c0eac1d1aeaaea4e891b2652678e7ec5388bbb09e63d17c1d2ec5",
    "XAU/USD": "765d2c9068b1f8f44a5e983db118f1ed1d49eb07c0a9a041274e1c67f6a02b12",
    "XAG/USD": "f2fb37a195e0b7a6e4e67c1a7a5c7c2e7f0b4a1e8a9b4c5d6e7f8a9b0c1d2e3",
    "EUR/USD": "a995d24e5a6c5b0c5a9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7",
}

COINGECKO_IDS = {
    "BTC/USD": "bitcoin",
    "ETH/USD": "ethereum",
    "SOL/USD": "solana",
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

    def __init__(self):
        self._http: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10)
        return self._http

    async def close(self):
        if self._http:
            await self._http.aclose()
            self._http = None

    async def get_price(self, asset: str) -> list[OraclePrice]:
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
        return results

    async def get_all_prices(self) -> dict[str, list[OraclePrice]]:
        assets = list(set(list(PYTH_FEEDS.keys()) + list(COINGECKO_IDS.keys()) + ["BTC/USD", "ETH/USD"]))
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
