import sys
import os
import pytest
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestProviderRegistry:
    def test_discover_providers(self):
        from core.provider_registry import ProviderRegistry
        registry = ProviderRegistry()
        discovered = registry.discover()
        assert len(discovered) >= 4
        assert "polymarket" in discovered
        assert "kalshi" in discovered
        assert "predictit" in discovered
        assert "manifold" in discovered

    def test_register_provider(self):
        from core.provider_registry import ProviderRegistry
        from providers.polymarket_edge import PolymarketEdgeProvider
        registry = ProviderRegistry()
        registry.register(PolymarketEdgeProvider())
        assert registry.get("polymarket") is not None
        assert len(registry.list_all()) == 1

    def test_stake_unstake(self):
        from core.provider_registry import ProviderRegistry
        from providers.polymarket_edge import PolymarketEdgeProvider
        registry = ProviderRegistry()
        registry.register(PolymarketEdgeProvider())
        assert registry.stake("polymarket", 100)
        provider = registry.get("polymarket")
        assert provider.reputation.staked_hbar == 100
        assert registry.unstake("polymarket", 50)
        assert provider.reputation.staked_hbar == 50
        assert not registry.unstake("polymarket", 100)


class TestRateLimiter:
    def test_rate_limit_predictit(self):
        from core.rate_limiter import rate_limiter
        assert not rate_limiter.is_rate_limited("predictit")
        assert rate_limiter.is_rate_limited("predictit")

    def test_rate_limit_polymarket(self):
        from core.rate_limiter import rate_limiter
        for _ in range(10):
            assert not rate_limiter.is_rate_limited("polymarket")
        assert rate_limiter.is_rate_limited("polymarket")

    def test_unknown_key(self):
        from core.rate_limiter import rate_limiter
        assert not rate_limiter.is_rate_limited("unknown")
        assert rate_limiter.get_remaining("unknown") == -1


class TestResponseCache:
    def test_cache_set_get(self):
        from core.cache import response_cache
        response_cache.set("test", {"query": "test"}, {"data": "test"})
        result = response_cache.get("test", {"query": "test"})
        assert result == {"data": "test"}

    def test_cache_miss(self):
        from core.cache import response_cache
        result = response_cache.get("test", {"query": "nonexistent"})
        assert result is None

    def test_cache_invalidate(self):
        from core.cache import response_cache
        response_cache.set("test", {"query": "test"}, {"data": "test"})
        response_cache.invalidate("test")
        result = response_cache.get("test", {"query": "test"})
        assert result is None

    def test_cache_stats(self):
        from core.cache import response_cache
        response_cache.set("test", {"query": "stats"}, {"data": "stats"}, ttl=0)
        stats = response_cache.get_stats()
        assert stats["total_entries"] >= 1


class TestAuction:
    def test_create_auction(self):
        from core.auction import ReverseAuction, AuctionBid
        auction = ReverseAuction("test-1", {"query": "test"})
        auction.add_bid(AuctionBid(provider_id="p1", cost_hbar=0.5, trust_score=80))
        auction.add_bid(AuctionBid(provider_id="p2", cost_hbar=0.3, trust_score=60))
        winner = auction.select_winner()
        assert winner is not None
        assert winner.provider_id in ["p1", "p2"]

    def test_empty_auction(self):
        from core.auction import ReverseAuction
        auction = ReverseAuction("test-2", {"query": "test"})
        winner = auction.select_winner()
        assert winner is None

    def test_bid_score_computation(self):
        from core.auction import ReverseAuction, AuctionBid
        auction = ReverseAuction("test-3", {"query": "test"})
        bid = AuctionBid(provider_id="p1", cost_hbar=0.1, trust_score=90, estimated_time_ms=100)
        score = auction.compute_bid_score(bid)
        assert 0 <= score <= 1


class TestStaking:
    def test_slash_provider(self):
        from core.staking import StakingManager
        from providers.polymarket_edge import PolymarketEdgeProvider
        manager = StakingManager()
        provider = PolymarketEdgeProvider()
        provider.reputation.staked_hbar = 100
        event = manager.slash_provider(provider, "Test", "low")
        assert event.slashed_amount > 0
        assert provider.reputation.staked_hbar < 100

    def test_slash_below_min(self):
        from core.staking import StakingManager
        from providers.polymarket_edge import PolymarketEdgeProvider
        manager = StakingManager()
        provider = PolymarketEdgeProvider()
        provider.reputation.staked_hbar = 5
        event = manager.slash_provider(provider, "Test", "low")
        assert event.slashed_amount == 0

    def test_risk_level(self):
        from core.staking import StakingManager
        from providers.polymarket_edge import PolymarketEdgeProvider
        manager = StakingManager()
        provider = PolymarketEdgeProvider()
        provider.reputation.staked_hbar = 100
        manager.slash_provider(provider, "Test", "high")
        risk = manager.get_provider_risk_level(provider)
        assert risk in ["low", "medium", "high", "critical"]


class TestAgentRegistry:
    def test_health_check(self):
        from core.config import Settings
        from core.hedera_manager import HederaManager
        from core.provider_registry import ProviderRegistry
        from core.agent_registry import AgentRegistry
        settings = Settings()
        hedera = HederaManager(settings)
        registry = ProviderRegistry()
        agent = AgentRegistry(settings, hedera, registry)
        health = agent.get_health_check()
        assert health.status in ["healthy", "degraded"]
        assert health.uptime_seconds >= 0
        assert health.providers_count == 0

    def test_request_count(self):
        from core.config import Settings
        from core.hedera_manager import HederaManager
        from core.provider_registry import ProviderRegistry
        from core.agent_registry import AgentRegistry
        settings = Settings()
        hedera = HederaManager(settings)
        registry = ProviderRegistry()
        agent = AgentRegistry(settings, hedera, registry)
        agent.increment_request_count()
        agent.increment_request_count()
        assert agent._total_requests_served == 2


class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        from core.websocket_manager import WebSocketManager
        manager = WebSocketManager()
        assert manager.active_connections == 0


class TestHederaManager:
    def test_generate_request_id(self):
        from core.config import Settings
        from core.hedera_manager import HederaManager
        settings = Settings()
        hedera = HederaManager(settings)
        rid = hedera.generate_request_id()
        assert len(rid) > 0

    def test_payment_memo(self):
        from core.config import Settings
        from core.hedera_manager import HederaManager
        settings = Settings()
        hedera = HederaManager(settings)
        memo = hedera.generate_payment_memo("123", "polymarket")
        parsed = hedera.parse_payment_memo(memo)
        assert parsed["request_id"] == "123"
        assert parsed["provider_id"] == "polymarket"

    def test_compute_data_hash(self):
        from core.config import Settings
        from core.hedera_manager import HederaManager
        settings = Settings()
        hedera = HederaManager(settings)
        h1 = hedera.compute_data_hash({"a": 1})
        h2 = hedera.compute_data_hash({"a": 1})
        h3 = hedera.compute_data_hash({"a": 2})
        assert h1 == h2
        assert h1 != h3


class TestOracleHub:
    def test_oracle_price_model(self):
        from core.oracle_hub import OraclePrice
        p = OraclePrice("pyth", "BTC/USD", 50000.0, 0.01, 1000)
        assert p.source == "pyth"
        assert p.source_name == "Pyth Network"
        assert p.price == 50000.0
        d = p.to_dict()
        assert d["source_name"] == "Pyth Network"

    def test_pyth_feed_ids(self):
        from core.oracle_hub import PYTH_FEEDS
        assert "BTC/USD" in PYTH_FEEDS
        assert "ETH/USD" in PYTH_FEEDS
        assert "XAU/USD" in PYTH_FEEDS
        assert len(PYTH_FEEDS["BTC/USD"]) == 64

    def test_coingecko_ids(self):
        from core.oracle_hub import COINGECKO_IDS
        assert COINGECKO_IDS["BTC/USD"] == "bitcoin"
        assert COINGECKO_IDS["ETH/USD"] == "ethereum"
        assert len(COINGECKO_IDS) >= 15

    def test_oracle_names(self):
        from core.oracle_hub import ORACLE_NAMES
        assert ORACLE_NAMES["pyth"] == "Pyth Network"
        assert ORACLE_NAMES["coingecko"] == "CoinGecko"


class TestArbitrageEngine:
    def test_arbitrage_signal_to_dict(self):
        from core.arbitrage_engine import ArbitrageSignal
        from core.oracle_hub import OraclePrice
        p1 = OraclePrice("pyth", "BTC/USD", 50000.0, 0.01, 1000)
        p2 = OraclePrice("coingecko", "BTC/USD", 50100.0, None, 1000)
        signal = ArbitrageSignal("BTC/USD", [p1, p2])
        assert signal.asset == "BTC/USD"
        d = signal.to_dict()
        assert d["asset"] == "BTC/USD"
        assert len(d["prices"]) == 2
        assert d["buy_from"] is None  # not computed until scan_asset

    def test_arbitrage_single_oracle(self):
        from core.arbitrage_engine import ArbitrageSignal
        from core.oracle_hub import OraclePrice
        p1 = OraclePrice("pyth", "BTC/USD", 50000.0, 0.01, 1000)
        signal = ArbitrageSignal("BTC/USD", [p1])
        assert signal.analysis is None  # not computed until scan_asset


class TestVerifiedFeed:
    def test_verification_levels(self):
        from core.verified_feed import _verification
        assert _verification(0.8, 3) == "high"
        assert _verification(0.5, 2) == "medium"
        assert _verification(0.3, 1) == "low"
        assert _verification(0.9, 5) == "high"

    def test_confidence_from_iqr(self):
        from core.verified_feed import _confidence_from_iqr
        vals = [0.5, 0.51, 0.49, 0.52, 0.48]
        c = _confidence_from_iqr(vals, 0.5)
        assert 0.0 <= c <= 1.0
        assert c >= 0.5

    def test_agreement_score(self):
        from core.verified_feed import _agreement
        assert _agreement([1.0, 1.0, 1.0]) == 1.0
        assert _agreement([0.5, 0.51]) > 0.9

    def test_median(self):
        from core.verified_feed import _median
        assert _median([1, 2, 3]) == 2
        assert _median([1, 2]) == 1.5
        assert _median([]) == 0.0


class TestFeedSchemas:
    def test_feed_request_model(self):
        from models.schemas import FeedRequest
        r = FeedRequest(topic="BTC/USD")
        assert r.topic == "BTC/USD"
        assert r.min_confidence is None

    def test_verified_price_point(self):
        from models.schemas import VerifiedPricePoint
        p = VerifiedPricePoint(asset="BTC/USD", price=50000.0, confidence=0.95, sources=3, agreement=0.98, timestamp=1000)
        assert p.asset == "BTC/USD"
        assert p.price == 50000.0

    def test_verified_data_feed(self):
        from models.schemas import VerifiedDataFeed, VerifiedPricePoint, SourceFeedBack
        agg = VerifiedPricePoint(asset="BTC/USD", price=50000.0, confidence=0.95, sources=3, agreement=0.98, timestamp=1000)
        src = SourceFeedBack(provider_id="pyth", provider_name="Pyth", price=50000.0, weight=0.9, success=True)
        feed = VerifiedDataFeed(feed_id="f1", topic="BTC/USD", aggregate=agg, sources=[src], verification="high")
        assert feed.feed_id == "f1"
        assert feed.verification == "high"

    def test_source_feedback(self):
        from models.schemas import SourceFeedBack
        s = SourceFeedBack(provider_id="kalshi", provider_name="Kalshi", price=0.5, weight=0.8, success=True)
        assert s.success
        assert s.error is None
        s2 = SourceFeedBack(provider_id="bad", provider_name="Bad", weight=0.0, success=False, error="fail")
        assert not s2.success


class TestTaskManager:
    def test_create_task(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        task = mgr.create_task()
        assert task.task_id is not None
        assert task.status.value == "submitted"

    def test_task_lifecycle(self):
        from core.task_manager import TaskManager
        from models.schemas import TaskStatus
        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.start_working(task.task_id)
        assert mgr.get_task(task.task_id).status == TaskStatus.WORKING
        artifact = mgr.complete(task.task_id, summary="Done")
        assert artifact is not None
        assert mgr.get_task(task.task_id).status == TaskStatus.COMPLETED

    def test_fail_task(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.fail(task.task_id, "Something broke")
        from models.schemas import TaskStatus
        assert mgr.get_task(task.task_id).status == TaskStatus.FAILED

    def test_add_parts(self):
        from core.task_manager import TaskManager
        from models.schemas import MessagePart, PartType
        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.add_text(task.task_id, "Hello")
        assert mgr.add_data(task.task_id, {"key": "value"})
        assert len(mgr.get_task(task.task_id).parts) == 2

    def test_artifacts(self):
        from core.task_manager import TaskManager
        from models.schemas import MessagePart, PartType
        mgr = TaskManager()
        task = mgr.create_task()
        parts = [MessagePart(type=PartType.TEXT, text="result")]
        art = mgr.add_artifact(task.task_id, parts)
        assert art is not None
        assert len(mgr.list_artifacts(task.task_id)) == 1
        assert mgr.get_artifact(art.artifact_id) is not None

    def test_count_by_status(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        mgr.create_task()
        t2 = mgr.create_task()
        mgr.start_working(t2.task_id)
        counts = mgr.count_by_status()
        assert counts.get("submitted", 0) >= 1
        assert counts.get("working", 0) >= 1

    def test_list_tasks_filter(self):
        from core.task_manager import TaskManager
        from models.schemas import TaskStatus
        mgr = TaskManager()
        t1 = mgr.create_task()
        t2 = mgr.create_task()
        mgr.start_working(t1.task_id)
        working = mgr.list_tasks(status=TaskStatus.WORKING)
        assert len(working) >= 1
        submitted = mgr.list_tasks(status=TaskStatus.SUBMITTED)
        assert len(submitted) >= 1

    def test_get_task_summary(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        task = mgr.create_task()
        mgr.add_text(task.task_id, "processing")
        mgr.complete(task.task_id, "all done")
        summary = mgr.get_task_summary(task.task_id)
        assert summary is not None
        assert summary["status"] == "completed"
        assert len(summary["artifacts"]) == 1


class TestContextManager:
    def test_create_context(self):
        from core.context_manager import ContextManager
        ctx = ContextManager()
        c = ctx.create_context()
        assert c.context_id is not None
        assert c.interaction_count == 0

    def test_add_interaction(self):
        from core.context_manager import ContextManager
        ctx = ContextManager()
        c = ctx.create_context()
        assert ctx.add_interaction(c.context_id, "task-1", "Fetched BTC price")
        assert ctx.get_context(c.context_id).interaction_count == 1
        history = ctx.get_interactions(c.context_id)
        assert len(history) == 1

    def test_compact_summary(self):
        from core.context_manager import ContextManager
        ctx = ContextManager()
        c = ctx.create_context()
        ctx.add_interaction(c.context_id, "t1", "Got BTC price $78k")
        ctx.add_interaction(c.context_id, "t2", "Arbitrage spread 0.02%")
        summary = ctx.get_compact_summary(c.context_id)
        assert summary is not None
        assert summary["interaction_count"] == 2
        assert "Arbitrage" in summary["summary"]

    def test_fork_context(self):
        from core.context_manager import ContextManager
        ctx = ContextManager()
        parent = ctx.create_context()
        ctx.add_interaction(parent.context_id, "t1", "Research done")
        child = ctx.fork_context(parent.context_id)
        assert child is not None
        assert child.parent_context_id == parent.context_id
        assert child.interaction_count == 1

    def test_context_persistence(self):
        from core.context_manager import ContextManager
        ctx = ContextManager(max_history=3)
        c = ctx.create_context()
        for i in range(5):
            ctx.add_interaction(c.context_id, f"t{i}", f"Interaction {i}")
        history = ctx.get_interactions(c.context_id)
        assert len(history) == 3
    def test_create_task(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        task = mgr.create_task()
        assert task.task_id is not None
        assert task.status.value == "submitted"

    def test_task_lifecycle(self):
        from core.task_manager import TaskManager
        from models.schemas import TaskStatus
        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.start_working(task.task_id)
        assert mgr.get_task(task.task_id).status == TaskStatus.WORKING
        artifact = mgr.complete(task.task_id, summary="Done")
        assert artifact is not None
        assert mgr.get_task(task.task_id).status == TaskStatus.COMPLETED

    def test_fail_task(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.fail(task.task_id, "Something broke")
        from models.schemas import TaskStatus
        assert mgr.get_task(task.task_id).status == TaskStatus.FAILED

    def test_add_parts(self):
        from core.task_manager import TaskManager
        from models.schemas import MessagePart, PartType
        mgr = TaskManager()
        task = mgr.create_task()
        assert mgr.add_text(task.task_id, "Hello")
        assert mgr.add_data(task.task_id, {"key": "value"})
        assert len(mgr.get_task(task.task_id).parts) == 2

    def test_artifacts(self):
        from core.task_manager import TaskManager
        from models.schemas import MessagePart, PartType
        mgr = TaskManager()
        task = mgr.create_task()
        parts = [MessagePart(type=PartType.TEXT, text="result")]
        art = mgr.add_artifact(task.task_id, parts)
        assert art is not None
        assert len(mgr.list_artifacts(task.task_id)) == 1
        assert mgr.get_artifact(art.artifact_id) is not None

    def test_count_by_status(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        mgr.create_task()
        t2 = mgr.create_task()
        mgr.start_working(t2.task_id)
        counts = mgr.count_by_status()
        assert counts.get("submitted", 0) >= 1
        assert counts.get("working", 0) >= 1

    def test_list_tasks_filter(self):
        from core.task_manager import TaskManager
        from models.schemas import TaskStatus
        mgr = TaskManager()
        t1 = mgr.create_task()
        t2 = mgr.create_task()
        mgr.start_working(t1.task_id)
        working = mgr.list_tasks(status=TaskStatus.WORKING)
        assert len(working) >= 1
        submitted = mgr.list_tasks(status=TaskStatus.SUBMITTED)
        assert len(submitted) >= 1

    def test_get_task_summary(self):
        from core.task_manager import TaskManager
        mgr = TaskManager()
        task = mgr.create_task()
        mgr.add_text(task.task_id, "processing")
        mgr.complete(task.task_id, "all done")
        summary = mgr.get_task_summary(task.task_id)
        assert summary is not None
        assert summary["status"] == "completed"
        assert len(summary["artifacts"]) == 1

