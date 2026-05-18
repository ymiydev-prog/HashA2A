import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from core.config import Settings
from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.oracle_hub import OracleHub
from core.arbitrage_engine import ArbitrageEngine
from core.pricing import PricingConverter
from core.x402 import X402Handler, X402HederaHandler
from api.deps import get_hedera_manager, get_payment_engine, get_settings
from models.schemas import PaymentRequest, RequestStatus
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feeds", tags=["feeds"])

_feed_cache: dict[str, dict[str, Any]] = {}
_feed_pending: dict[str, str] = {}

hub: OracleHub | None = None
arb_engine: ArbitrageEngine | None = None
x402: X402Handler | None = None
x402_hedera: X402HederaHandler | None = None


def init_feeds(settings: Settings):
    global hub, arb_engine, x402, x402_hedera
    hub = OracleHub()
    arb_engine = ArbitrageEngine(hub)
    x402 = X402Handler(
        treasury_address=settings.treasury_account or settings.hedera_operator_id,
    )
    if settings.x402_hedera_facilitator:
        x402_hedera = X402HederaHandler(
            pay_to=settings.treasury_account or settings.hedera_operator_id,
            fee_payer=settings.x402_hedera_facilitator,
            asset="0.0.0",
            network=settings.x402_hedera_network,
            facilitator_url=settings.x402_hedera_facilitator,
        )


def _get_prices_key(asset: str, source: str | None) -> str:
    return f"{asset}:{source or 'all'}"


class PriceQuery(BaseModel):
    asset: str = Field(..., description="Asset symbol, e.g. BTC/USD, ETH/USD")
    source: str | None = Field(default=None, description="Oracle source: pyth, coingecko, defillama, or all")


class ArbitrageScanQuery(BaseModel):
    min_spread: float | None = Field(default=None, ge=0.0, description="Minimum spread percentage")


@router.post("/prices")
async def get_prices(body: PriceQuery, request: Request):
    if not hub:
        init_feeds(request.app.state.settings)
    prices = await hub.get_price(body.asset.upper())
    if not prices:
        raise HTTPException(status_code=404, detail=f"No prices available for {body.asset}")
    if body.source:
        prices = [p for p in prices if p.source == body.source.lower()]
        if not prices:
            raise HTTPException(status_code=404, detail=f"No prices from {body.source} for {body.asset}")

    results = [p.to_dict() for p in prices]
    key = _get_prices_key(body.asset, body.source)
    _feed_pending[key] = "paid"

    pricing = PricingConverter()
    usdc_cost = 0.25
    hbar_cost = await pricing.usdc_to_hbar(usdc_cost)
    payment = x402.build_402_response(str(request.url), usdc_cost, f"Price feed: {body.asset}")

    return {
        "asset": body.asset.upper(),
        "prices": results,
        "oracles_consulted": len(results),
        "price": prices[0].price if len(results) == 1 else None,
        "payment": {
            "hbar": {"amount": hbar_cost, "hip991": True},
            "usdc": {"amount": usdc_cost, "protocol": "x402", "accept": payment[1].get("PAYMENT-REQUIRED")},
        },
        "instructions": "Pay USDC (fixed) or HBAR (calculated live from HBAR/USD rate)",
    }


@router.post("/arbitrage")
async def scan_arbitrage(body: ArbitrageScanQuery, request: Request):
    if not arb_engine:
        init_feeds(request.app.state.settings)
    signals = await arb_engine.scan_all()
    if body.min_spread:
        signals = [s for s in signals if s.spread_pct >= body.min_spread]

    pricing = PricingConverter()
    usdc_cost = 0.50
    hbar_cost = await pricing.usdc_to_hbar(usdc_cost)
    payment = x402.build_402_response(str(request.url), usdc_cost, "Arbitrage scan")

    return {
        "signals": [s.to_dict() for s in signals if s.opportunity != "low"],
        "total_scanned": len(signals),
        "timestamp": int(time.time()),
        "payment": {
            "hbar": {"amount": hbar_cost, "hip991": True},
            "usdc": {"amount": usdc_cost, "protocol": "x402", "accept": payment[1].get("PAYMENT-REQUIRED")},
        },
    }


@router.get("/verify/{asset}")
async def verify_arbitrage(asset: str, request: Request):
    if not arb_engine:
        init_feeds(request.app.state.settings)
    signal = await arb_engine.scan_asset(asset.upper())
    pricing = PricingConverter()
    usdc_cost = 0.10
    hbar_cost = await pricing.usdc_to_hbar(usdc_cost)
    payment = x402.build_402_response(str(request.url), usdc_cost, f"Arbitrage verify: {asset}")
    return {
        "signal": signal.to_dict(),
        "payment": {
            "hbar": {"amount": hbar_cost, "hip991": True},
            "usdc": {"amount": usdc_cost, "protocol": "x402", "accept": payment[1].get("PAYMENT-REQUIRED")},
        },
    }


@router.post("/x402/verify")
async def verify_x402_payment(payload: dict):
    if not x402:
        raise HTTPException(status_code=500, detail="x402 not initialized")
    verified, msg = await x402.verify_payment(payload)
    if not verified:
        raise HTTPException(status_code=402, detail=msg)
    key = _feed_pending.pop(payload.get("resource", ""), None) or "verified"
    return {"status": "paid", "access_key": key}


@router.post("/x402/hedera/verify")
async def verify_x402_hedera_payment(payload: dict):
    if not x402_hedera:
        raise HTTPException(status_code=500, detail="x402 Hedera rail not configured")
    verified, msg = await x402_hedera.verify_payment(payload)
    if not verified:
        raise HTTPException(status_code=402, detail=msg)
    return {"status": "paid", "access_key": "verified", "rail": "hedera"}


@router.get("/x402/manifest")
async def x402_manifest():
    pricing = PricingConverter()
    prices = await pricing.get_prices()
    manifest = {
        "protocol": "x402 v2",
        "rails": {
            "base_usdc": {
                "network": "eip155:8453",
                "asset": "USDC",
                "pricing": {
                    "price_feed": f"${prices['products']['price_feed']['usdc']} USDC",
                    "arbitrage_scan": f"${prices['products']['arbitrage_scan']['usdc']} USDC",
                    "arbitrage_verify": f"${prices['products']['arbitrage_verify']['usdc']} USDC",
                },
            },
        },
        "rate": prices["rates"],
    }
    if x402_hedera:
        manifest["rails"]["hedera"] = {
            "network": x402_hedera.network,
            "asset": "HBAR" if x402_hedera.asset == "0.0.0" else x402_hedera.asset,
            "payTo": x402_hedera.pay_to,
            "feePayer": x402_hedera.fee_payer,
            "scheme": "exact",
        }
    return manifest


@router.get("/pricing")
async def get_pricing():
    """Real-time pricing: USDC fixed, HBAR calculated from live HBAR/USD rate."""
    pricing = PricingConverter()
    return await pricing.get_prices()
