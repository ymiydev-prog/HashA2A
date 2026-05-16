"""End-to-end tests against live APIs (requires network + server running)."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

pytestmark = pytest.mark.e2e


class TestOracleHubE2E:
    """Tests real oracle API calls (Pyth, CoinGecko, DeFiLlama)."""

    def test_pyth_btc_price(self):
        import asyncio
        from core.oracle_hub import OracleHub

        async def t():
            hub = OracleHub()
            prices = await hub.get_price("BTC/USD")
            await hub.close()
            return prices

        prices = asyncio.run(t())
        assert len(prices) >= 1
        pyth = [p for p in prices if p.source == "pyth"]
        assert len(pyth) >= 1
        assert pyth[0].price > 10000

    def test_coingecko_eth_price(self):
        import asyncio
        from core.oracle_hub import OracleHub

        async def t():
            hub = OracleHub()
            prices = await hub.get_price("ETH/USD")
            await hub.close()
            return prices

        prices = asyncio.run(t())
        cg = [p for p in prices if p.source == "coingecko"]
        assert len(cg) >= 1
        assert cg[0].price > 100

    def test_gold_price_from_pyth(self):
        import asyncio
        from core.oracle_hub import OracleHub

        async def t():
            hub = OracleHub()
            prices = await hub.get_price("XAU/USD")
            await hub.close()
            return prices

        prices = asyncio.run(t())
        assert len(prices) >= 1
        assert prices[0].price > 500

    def test_all_assets_return_prices(self):
        import asyncio
        from core.oracle_hub import OracleHub

        async def t():
            hub = OracleHub()
            assets = await hub.get_all_prices()
            await hub.close()
            return assets

        assets = asyncio.run(t())
        assert len(assets) >= 3
        assert "BTC/USD" in assets or "ETH/USD" in assets


class TestArbitrageE2E:
    """Tests arbitrage engine with real data."""

    def test_scan_btc_spread(self):
        import asyncio
        from core.oracle_hub import OracleHub
        from core.arbitrage_engine import ArbitrageEngine

        async def t():
            hub = OracleHub()
            engine = ArbitrageEngine(hub)
            signal = await engine.scan_asset("BTC/USD")
            await hub.close()
            return signal

        signal = asyncio.run(t())
        assert len(signal.prices) >= 2
        assert signal.asset == "BTC/USD"
        assert signal.spread_pct >= 0

    def test_scan_all_arbitrages(self):
        import asyncio
        from core.oracle_hub import OracleHub
        from core.arbitrage_engine import ArbitrageEngine

        async def t():
            hub = OracleHub()
            engine = ArbitrageEngine(hub)
            signals = await engine.scan_all()
            await hub.close()
            return signals

        signals = asyncio.run(t())
        assert len(signals) >= 3


class TestPricingE2E:
    """Tests pricing converter with live HBAR rate."""

    def test_hbar_price_from_coingecko(self):
        import asyncio
        from core.pricing import PricingConverter

        async def t():
            p = PricingConverter()
            rate = await p.get_hbars_per_usd()
            return rate

        rate = asyncio.run(t())
        assert rate > 0
        assert rate < 100  # sanity: 1 USD should be < 100 HBAR

    def test_usdc_to_hbar_conversion(self):
        import asyncio
        from core.pricing import PricingConverter

        async def t():
            p = PricingConverter()
            hbar = await p.usdc_to_hbar(1.0)
            prices = await p.get_prices()
            return hbar, prices

        hbar, prices = asyncio.run(t())
        assert hbar > 0
        assert "products" in prices
        assert "price_feed" in prices["products"]


class TestTaskLifecycleE2E:
    """Tests A2A task lifecycle end-to-end."""

    def test_create_and_complete(self):
        from core.task_manager import TaskManager
        from models.schemas import TaskStatus

        mgr = TaskManager()
        task = mgr.create_task()
        assert task.status == TaskStatus.SUBMITTED
        assert mgr.start_working(task.task_id)
        assert mgr.get_task(task.task_id).status == TaskStatus.WORKING
        artifact = mgr.complete(task.task_id, summary="E2E test completed")
        assert artifact is not None
        assert mgr.get_task(task.task_id).status == TaskStatus.COMPLETED

    def test_context_lifecycle(self):
        from core.context_manager import ContextManager

        ctx = ContextManager()
        c = ctx.create_context()
        assert ctx.add_interaction(c.context_id, "t1", "E2E test")
        summary = ctx.get_compact_summary(c.context_id)
        assert summary is not None
        assert summary["interaction_count"] == 1

        child = ctx.fork_context(c.context_id)
        assert child is not None
        assert child.parent_context_id == c.context_id

    def test_add_text_and_data_parts(self):
        from core.task_manager import TaskManager
        from models.schemas import MessagePart, PartType

        mgr = TaskManager()
        task = mgr.create_task()
        mgr.add_text(task.task_id, "E2E text")
        mgr.add_data(task.task_id, {"key": "value"})
        updated = mgr.get_task(task.task_id)
        assert len(updated.parts) == 2

    def test_request_input_state(self):
        from core.task_manager import TaskManager
        from models.schemas import TaskStatus

        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.request_input(task.task_id, "Need more data")
        assert mgr.get_task(task.task_id).status == TaskStatus.INPUT_REQUIRED


class TestJwtE2E:
    """Tests JWT token creation and verification."""

    def test_create_jwt_token(self):
        from core.auth import create_token, verify_token

        token = create_token(agent_id="test-agent", ttl=300, scopes=["read", "trade"])
        assert token is not None
        assert len(token) > 20

        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-agent"

    def test_expired_token_rejected(self):
        from core.auth import create_token, verify_token
        import time

        token = create_token(agent_id="test", ttl=1)
        time.sleep(1.5)
        payload = verify_token(token)
        assert payload is None or payload.get("sub") != "test"


class TestMandateE2E:
    """Tests AP2 cryptographic mandates."""

    def test_create_and_authorize(self):
        from core.auth import MandateManager

        mgr = MandateManager()
        mandate = mgr.create_mandate("intent", "agent-1", max_spend_usdc=50.0, ttl=86400)
        assert mandate.is_valid()
        assert mgr.authorize(mandate.mandate_id, 10.0)
        remaining = mgr.to_dict(mandate)["remaining"]
        assert remaining == 40.0

    def test_mandate_exhausted(self):
        from core.auth import MandateManager

        mgr = MandateManager()
        m = mgr.create_mandate("cart", "agent-2", max_spend_usdc=5.0, ttl=86400)
        assert mgr.authorize(m.mandate_id, 5.0)
        assert not mgr.authorize(m.mandate_id, 1.0)
