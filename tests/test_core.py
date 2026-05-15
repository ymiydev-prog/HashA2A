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
