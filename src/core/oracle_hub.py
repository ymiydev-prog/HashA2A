"""OracleHub — connects to Pyth, CoinGecko, DeFiLlama, and Binance."""
import asyncio
import time
from typing import Any

import httpx


# ── Pyth Hermes price feed IDs ──────────────────────────────────────────
PYTH_FEEDS = {
    # Crypto
    "BTC/USD": "e62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    "ETH/USD": "ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
    "SOL/USD": "ef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
    "HBAR/USD": "3728e591097635310e6341af53db8b7ee42da9b3a8d918f9463ce9cca886dfbd",
    "BNB/USD": "2f95862b045670cd22bee3114c39763a4a08beeb663b145d283db31ebb0a0cf5",
    "XRP/USD": "84e2adc2d74aabb3392b0f98b960ed4b9a3cc1d37bdccfbb09c9588701df0794",
    "ADA/USD": "2a01deaec9e51a579677b2e815f71b2697a0e18fee7b47b855e9294c4e2cfbaa",
    "DOGE/USD": "dcef50dd0a4cd2dcc17e45df1676dcb336a11a61c69df7a0299b0150c672d25c",
    "AVAX/USD": "93da3352f9f1d105fdfe4971cfa80e9dd777bfc5d0f683ebb6e1294b92137bb4",
    "DOT/USD": "ca3eed9b267293f6595901c734c7525ce8ef49afe1d5a62f1e77a8f1d5bc0e3e",
    "LINK/USD": "8ac0c70fff57e9a4dfd5d9f10d41293f56a5afb9fb93888f14c3a02fb7005a80",
    "UNI/USD": "d780ae9c7c1a0e336508851de2fa96b6478e3f434d03fd01adde0dd09c166050",
    "MATIC/USD": "5de33a9112c2a92a8eb59d0a1c3bb3a723c7893ab1ce6777d2eca496082ae9e2",
    "LTC/USD": "6e3f3e8250ba00a8d9ef66e91b1849b5593b5ffc3e13deb79a8dd38f41c6753e",
    "AAVE/USD": "9388fefbe0c503698be5f1bd641ea462c6c09b632215ff003398efdb975ca888",
    "ATOM/USD": "b00b7ac2d2a7efbb34c968bd7b5b1850115af6276b0f18c61959bd1c27f604a7",
    "ARB/USD": "3fa4252848f154e3cf6634fc5ec1b0b4ff82b66968132ccddacadd1f1524bd7a",
    "APT/USD": "30502b021faac1404e0ae6cfda0fec3d7bc1e131a3f78e450a5e2b415a55082f",
    "OP/USD": "385f64e1de66c0a44c09e5e71557df4fbb347109047d61b6909de1e2c31c4fbd",
    "SUI/USD": "23be19543ddcefc1aa340677be37ee93ae5e84dbb8c00d25f43a9e7d2e7a72a6",
    # Equities
    "AAPL/USD": "241b9a5ce1c3e4bfc68e377158328628f1b478afaa796c4b1760bd3713c2d2d2",
    "MSFT/USD": "8f98f8267ddddeeb61b4fd11f21dc0c2842c417622b4d685243fa73b5830131f",
    "NVDA/USD": "61c4ca5b9731a79e285a01e24432d57d89f0ecdd4cd7828196ca8992d5eafef6",
    "GOOGL/USD": "88d0800b1649d98e21b8bf9c3f42ab548034d62874ad5d80e1c1b730566d7f61",
    "AMZN/USD": "62731dfcc8b8542e52753f208248c3e73fab2ec15422d6f65c2decda71ccea0d",
    "TSLA/USD": "16dad506d7db8da01c87581c87ca897a012a153557d4d578c3b9c9e1bc0632f1",
    "META/USD": "78a3e3b8e676a8f73c439f5d749737034b139bbbe899ba5775216fba596607fe",
    # Commodities
    "XAU/USD": "765d2ba906dbc32ca17cc11f5310a89e9ee1f6420508c63861f2f8ba4ee34bb2",
    "XAG/USD": "f2fb02c32b055c805e7238d628e5e9dadef274376114eb1f012337cabe93871e",
    # Forex (major via Pyth)
    "USD/JPY": "ef2c98c804ba503c6a707e38be4dfbb16683775f195b091252bf24693042fd52",
}

COINGECKO_IDS = {
    # Crypto
    "BTC/USD": "bitcoin",
    "ETH/USD": "ethereum",
    "SOL/USD": "solana",
    "HBAR/USD": "hedera-hashgraph",
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
    "LTC/USD": "litecoin",
    "MATIC/USD": "polygon",
}

BINANCE_SYMBOLS = {
    "BTC/USD": "BTCUSDT",
    "ETH/USD": "ETHUSDT",
    "SOL/USD": "SOLUSDT",
    "HBAR/USD": "HBARUSDT",
    "BNB/USD": "BNBUSDT",
    "XRP/USD": "XRPUSDT",
    "ADA/USD": "ADAUSDT",
    "DOGE/USD": "DOGEUSDT",
    "AVAX/USD": "AVAXUSDT",
    "DOT/USD": "DOTUSDT",
    "LINK/USD": "LINKUSDT",
    "UNI/USD": "UNIUSDT",
    "AAVE/USD": "AAVEUSDT",
    "ATOM/USD": "ATOMUSDT",
    "ARB/USD": "ARBUSDT",
    "APT/USD": "APTUSDT",
    "OP/USD": "OPUSDT",
    "SUI/USD": "SUIUSDT",
    "LTC/USD": "LTCUSDT",
    "MATIC/USD": "MATICUSDT",
}

LLAMA_ASSETS = {
    "BTC/USD": "bitcoin",
    "ETH/USD": "ethereum",
    "SOL/USD": "solana",
    "HBAR/USD": "hedera-hashgraph",
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
    "LTC/USD": "litecoin",
    "MATIC/USD": "matic-network",
}

ORACLE_NAMES = {
    "pyth": "Pyth Network",
    "coingecko": "CoinGecko",
    "defillama": "DeFiLlama (Chainlink)",
    "binance": "Binance",
    "forex": "Foreign Exchange",
}


# ── Free forex rate API ─────────────────────────────────────────────────
FOREX_ASSETS = ["EUR/USD", "GBP/USD", "AUD/USD", "CAD/USD", "CHF/USD", "CNH/USD"]
FOREX_API_BASE = "https://open.er-api.com/v6/latest/USD"


class OraclePrice:
    def __init__(
        self,
        source: str,
        asset: str,
        price: float,
        confidence: float | None = None,
        timestamp: int = 0,
        change_24h: float | None = None,
        volume_24h: float | None = None,
        market_cap: float | None = None,
    ):
        self.source = source
        self.source_name = ORACLE_NAMES.get(source, source)
        self.asset = asset
        self.price = price
        self.confidence = confidence
        self.timestamp = timestamp or int(time.time())
        self.change_24h = change_24h
        self.volume_24h = volume_24h
        self.market_cap = market_cap

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "source_name": self.source_name,
            "asset": self.asset,
            "price": self.price,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "change_24h": self.change_24h,
            "volume_24h": self.volume_24h,
            "market_cap": self.market_cap,
        }


class OracleHub:
    """Fetches prices from multiple free oracle sources simultaneously."""

    def __init__(self, cache_ttl: int = 15):
        self._http: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[float, list[OraclePrice]]] = {}
        self._cache_ttl = cache_ttl

    @property
    def all_assets(self) -> list[str]:
        assets = set()
        assets.update(PYTH_FEEDS.keys())
        assets.update(COINGECKO_IDS.keys())
        assets.update(BINANCE_SYMBOLS.keys())
        assets.update(LLAMA_ASSETS.keys())
        assets.update(FOREX_ASSETS)
        return sorted(assets)

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
        if asset in LLAMA_ASSETS:
            tasks.append(self._fetch_defillama(asset))
        if asset in BINANCE_SYMBOLS:
            tasks.append(self._fetch_binance(asset))
        if asset in FOREX_ASSETS:
            tasks.append(self._fetch_forex(asset))

        done = await asyncio.gather(*tasks, return_exceptions=True)
        for r in done:
            if isinstance(r, OraclePrice):
                results.append(r)

        if results:
            self._cache[asset] = (now, results)
        return results

    async def get_all_prices(self) -> dict[str, list[OraclePrice]]:
        assets = self.all_assets
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

    # ── Pyth Hermes ─────────────────────────────────────────────────────
    async def _fetch_pyth(self, asset: str) -> OraclePrice | None:
        feed_id = PYTH_FEEDS.get(asset)
        if not feed_id:
            return None
        try:
            c = await self._client()
            resp = await c.get(
                "https://hermes.pyth.network/v2/updates/price/latest",
                params={"ids[]": feed_id},
            )
            data = resp.json()
            parsed = data.get("parsed", [])
            if not parsed:
                return None
            p = parsed[0]["price"]
            price = float(p["price"]) * (10 ** p["expo"])
            conf = float(p["conf"]) * (10 ** p["expo"]) if p.get("conf") else None
            return OraclePrice(
                "pyth", asset, price, conf,
                timestamp=p["publish_time"],
            )
        except Exception:
            return None

    # ── CoinGecko ───────────────────────────────────────────────────────
    async def _fetch_coingecko(self, asset: str) -> OraclePrice | None:
        cg_id = COINGECKO_IDS.get(asset)
        if not cg_id:
            return None
        try:
            c = await self._client()
            resp = await c.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": cg_id,
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
            )
            data = resp.json()
            coin = data.get(cg_id, {})
            price = coin.get("usd")
            if price is None:
                return None
            return OraclePrice(
                "coingecko", asset, float(price),
                timestamp=int(time.time()),
                change_24h=coin.get("usd_24h_change"),
                volume_24h=coin.get("usd_24h_vol"),
                market_cap=coin.get("usd_market_cap"),
            )
        except Exception:
            return None

    # ── DeFiLlama (Chainlink proxy) ─────────────────────────────────────
    async def _fetch_defillama(self, asset: str) -> OraclePrice | None:
        llama_id = LLAMA_ASSETS.get(asset)
        if not llama_id:
            return None
        try:
            c = await self._client()
            resp = await c.get(
                f"https://coins.llama.fi/prices/current/coingecko:{llama_id}"
            )
            data = resp.json()
            coin = data.get("coins", {}).get(f"coingecko:{llama_id}")
            if not coin:
                return None
            return OraclePrice(
                "defillama", asset, float(coin["price"]),
                timestamp=coin.get("timestamp", 0),
            )
        except Exception:
            return None

    # ── Binance ─────────────────────────────────────────────────────────
    async def _fetch_binance(self, asset: str) -> OraclePrice | None:
        symbol = BINANCE_SYMBOLS.get(asset)
        if not symbol:
            return None
        try:
            c = await self._client()
            resp = await c.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": symbol},
            )
            data = resp.json()
            price = data.get("lastPrice")
            if price is None:
                return None
            return OraclePrice(
                "binance", asset, float(price),
                timestamp=int(data.get("closeTime", 0)) // 1000,
                change_24h=float(data.get("priceChangePercent", 0)),
                volume_24h=float(data.get("quoteVolume", 0)),
            )
        except Exception:
            return None

    # ── Free Forex API (open.er-api.com) ────────────────────────────────
    _forex_cache: dict[str, float] = {}
    _forex_cache_time: float = 0

    async def _fetch_forex(self, asset: str) -> OraclePrice | None:
        if asset not in FOREX_ASSETS:
            return None
        parts = asset.split("/")
        target_currency = parts[0]  # e.g. EUR from EUR/USD
        try:
            # Refresh rates cache every 60s
            now = time.time()
            if not self._forex_cache or now - self._forex_cache_time > 60:
                c = await self._client()
                resp = await c.get(FOREX_API_BASE)
                data = resp.json()
                rates = data.get("rates", {})
                self._forex_cache = {
                    "EUR": rates.get("EUR"),
                    "GBP": rates.get("GBP"),
                    "AUD": rates.get("AUD"),
                    "CAD": rates.get("CAD"),
                    "CHF": rates.get("CHF"),
                    "CNH": rates.get("CNY"),
                }
                self._forex_cache_time = now
            rate = self._forex_cache.get(target_currency)
            if rate is None:
                return None
            return OraclePrice("forex", asset, float(rate), timestamp=int(now))
        except Exception:
            return None