"""Pricing converter — USDC prices are fixed, HBAR prices calculated in real-time."""

import time
from typing import Any

import httpx


class PricingConverter:
    """Fetches HBAR/USD rate and converts USDC prices to HBAR in real-time."""

    FIXED_PRICING_USDC: dict[str, float] = {
        "price_feed": 0.25,
        "arbitrage_scan": 0.50,
        "arbitrage_verify": 0.10,
        "prediction_market": 0.15,
        "deep_research": 0.50,
        "aggregate": 1.00,
    }

    FIXED_PRICING_HBAR: dict[str, float] = {
        "prediction_market": 0.3,
        "deep_research": 1.0,
        "aggregate": 1.5,
    }

    def __init__(self):
        self._hbars_per_usd: float | None = None
        self._last_fetch: float = 0
        self._cache_ttl: float = 60.0

    async def get_hbars_per_usd(self) -> float:
        now = time.time()
        if self._hbars_per_usd is not None and (now - self._last_fetch) < self._cache_ttl:
            return self._hbars_per_usd
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": "hedera-hashgraph", "vs_currencies": "usd"},
                )
                data = resp.json()
                usd_price = data.get("hedera-hashgraph", {}).get("usd")
                if usd_price and usd_price > 0:
                    self._hbars_per_usd = 1.0 / usd_price
                else:
                    self._hbars_per_usd = self._hbars_per_usd or 5.0
        except Exception:
            self._hbars_per_usd = self._hbars_per_usd or 5.0
        self._last_fetch = now
        return self._hbars_per_usd

    async def usdc_to_hbar(self, usdc_amount: float) -> float:
        rate = await self.get_hbars_per_usd()
        raw = usdc_amount * rate
        return max(round(raw, 2), 0.01)

    async def get_prices(self) -> dict[str, Any]:
        """Returns all product prices in both USDC and HBAR."""
        hbar_rate = await self.get_hbars_per_usd()
        products = {}
        for key, usdc in self.FIXED_PRICING_USDC.items():
            hbar_fixed = self.FIXED_PRICING_HBAR.get(key)
            if hbar_fixed is not None:
                products[key] = {"usdc": usdc, "hbar": hbar_fixed}
            else:
                products[key] = {"usdc": usdc, "hbar": await self.usdc_to_hbar(usdc)}
        return {
            "products": products,
            "rates": {
                "hbar_per_usd": round(hbar_rate, 4),
                "usd_per_hbar": round(1.0 / hbar_rate, 4) if hbar_rate > 0 else 0,
                "updated_at": int(time.time()),
            },
        }
