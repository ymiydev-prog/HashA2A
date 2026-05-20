import json
from mcp.server.fastmcp import FastMCP

from core.config import Settings
from core.hedera_manager import HederaManager
from core.provider_registry import ProviderRegistry
from core.payment_engine import PaymentEngine
from core.agent_registry import AgentRegistry
from core.consensus_logger import ConsensusLogger


def create_mcp_server() -> FastMCP:
    settings = Settings()

    hedera = HederaManager(settings)
    provider_registry = ProviderRegistry()
    payment_engine = PaymentEngine(settings, hedera)
    consensus_logger = ConsensusLogger(hedera)
    agent_registry = AgentRegistry(settings, hedera, provider_registry)

    from providers.polymarket_edge import PolymarketEdgeProvider
    from providers.kalshi import KalshiBettingProvider
    from providers.predictit import PredictItProvider
    from providers.manifold import ManifoldMarketsProvider
    provider_registry.register(PolymarketEdgeProvider())
    provider_registry.register(KalshiBettingProvider())
    provider_registry.register(PredictItProvider())
    provider_registry.register(ManifoldMarketsProvider())
    provider_registry.discover()

    mcp = FastMCP(
        name="HashA2A",
        instructions=(
            "Agent-to-Agent Intelligence Layer. "
            "18 tools: multi-oracle price feeds, arbitrage scanning, asset profiles, "
            "deep research, Hedera Agent Kit enterprise plugin. "
            "36 assets across crypto (21), equities (7), commodities (2), forex (6). "
            "Pay per query via HBAR (HIP-991) or USDC (x402). "
            "Agent discovery: /.well-known/agent.json"
        ),
    )

    @mcp.tool(name="list_providers", description="List all available data providers with prices, trust scores, and staked amounts")
    def list_providers() -> str:
        caps = provider_registry.list_capabilities()
        lines = ["Available Data Providers:", ""]
        for p in caps:
            lines.append(f"  • {p.name} ({p.provider_id})")
            lines.append(f"    Price: {p.cost_hbar} HBAR per query")
            lines.append(f"    Trust Score: {p.trust_score:.0f}/100")
            lines.append(f"    Staked: {p.staked_hbar} HBAR")
            lines.append(f"    Success Rate: {p.success_rate:.0%}")
            lines.append("")
        return "\n".join(lines)

    @mcp.tool(name="get_market_data", description="Request processed market data from a provider. Returns payment instructions with the HCS topic ID where the agent must submit a message (HIP-991 auto-collects the fee).")
    def get_market_data(provider_id: str, query: str = "", limit: int = 10) -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        provider = provider_registry.get(provider_id)
        if not provider:
            return f"Error: Provider '{provider_id}' not found. Available: {[p.provider_id for p in provider_registry.list_all()]}"

        request_id = hedera.generate_request_id()
        inbound_topic = loop.run_until_complete(hedera.get_or_create_inbound_topic())

        from models.schemas import PaymentRequest
        import time
        payment = PaymentRequest(
            request_id=request_id,
            provider_id=provider.provider_id,
            amount_hbar=provider.cost_hbar,
            destination_account=hedera.settings.treasury_account,
            memo=f"HASHA2A:{request_id}:{provider.provider_id}",
            expires_at=int(time.time()) + hedera.settings.payment_ttl_seconds,
        )
        payment_engine.register_request(payment)

        lines = [
            f"To get data from {provider.name}:",
            "",
            f"1. Send a TopicMessageSubmitTransaction to topic: {inbound_topic}",
            f"   with message: {{\"request_id\": \"{request_id}\", \"provider\": \"{provider_id}\", \"params\": {{\"query\": \"{query}\", \"limit\": {limit}}}}}",
            f"2. HIP-991 will auto-collect {provider.cost_hbar} HBAR from your account",
            f"3. The fee is collected automatically — no separate transfer needed",
            "",
            f"4. Then poll GET /api/v1/requests/{request_id} until status='completed'",
            "",
            f"Request ID: {request_id}",
            f"Inbound Topic: {inbound_topic}",
        ]
        return "\n".join(lines)

    @mcp.tool(name="check_request", description="Check the status and result of a data request by its request ID.")
    def check_request(request_id: str) -> str:
        from api.routes.requests import _inflight
        completed = _inflight.get(request_id)
        if completed:
            data_summary = json.dumps(completed.data, indent=2)[:500] if completed.data else "N/A"
            return (
                f"Status: {completed.status.value}\n"
                f"Quality Score: {completed.quality_score}\n"
                f"Analysis:\n{completed.analysis}\n"
                f"Data: {data_summary}\n"
                f"HCS Proof: {completed.proof_tx_id}"
            )

        pending = payment_engine.get_pending(request_id)
        if pending:
            return f"Status: {pending.status.value}\nRequest ID: {request_id}"
        return f"Status: not_found\nRequest ID: {request_id} not found or expired"

    @mcp.tool(name="get_agent_profile", description="View the HashA2A agent profile including all supported providers, active HCS topics, and total requests served.")
    def get_agent_profile() -> str:
        profile_data = {
            "name": settings.agent_name,
            "version": settings.agent_version,
            "description": settings.agent_description,
            "tags": settings.agent_tags,
            "treasury_account": settings.treasury_account,
            "providers": [p.model_dump(mode="json") for p in provider_registry.list_capabilities()],
            "staked_hbar": sum(p.reputation.staked_hbar for p in provider_registry.list_all()),
        }
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            profile_data["inbound_topic"] = str(loop.run_until_complete(hedera.get_or_create_inbound_topic()))
            profile_data["audit_topic"] = str(loop.run_until_complete(hedera.get_or_create_audit_topic()))
        except Exception:
            pass

        return json.dumps(profile_data, indent=2)

    @mcp.tool(name="analyze_market", description="Run AI-powered analysis on a provider's market data using LangChain + OpenAI. Returns natural language insights about current probabilities, sentiment, and market conditions.")
    def analyze_market(provider_id: str) -> str:
        from core.ai_analyzer import AIAnalyzer

        provider = provider_registry.get(provider_id)
        if not provider:
            return f"Error: Provider '{provider_id}' not found."

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(provider.get_data({"request_id": hedera.generate_request_id()}))
        analyzer = AIAnalyzer(settings)
        analysis = analyzer.analyze(provider_id, result.data)

        if analysis:
            return f"AI Analysis for {provider.name}:\n\n{analysis}"
        return "Analysis unavailable (no API key or no data)."

    @mcp.tool(name="aggregate_market_data", description="Collect data from ALL prediction market providers simultaneously, cross-validate prices, and produce a unified intelligence report with verification score. Costs more but provides higher-quality verified data.")
    def aggregate_market_data(query: str = "latest markets") -> str:
        from core.ai_analyzer import AIAnalyzer
        from core.data_aggregator import DataAggregator

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        aggregator = DataAggregator(provider_registry, AIAnalyzer(settings), settings)
        result = loop.run_until_complete(aggregator.aggregate(
            request_id=hedera.generate_request_id(),
            query=query,
        ))

        lines = [
            f"=== Aggregated Intelligence Report ===",
            f"Query: {result.query}",
            f"Sources consulted: {result.consensus.total_sources}",
            f"Successful: {result.consensus.successful_sources}/{result.consensus.total_sources}",
            f"Agreement score: {result.consensus.agreement_score:.1%}",
            f"Verification score: {result.verification_score:.1%}",
            f"Total cost: {result.total_cost_hbar} HBAR",
            f"Processing time: {result.processing_time_ms:.0f}ms",
            f"",
            f"Sources:",
        ]
        for s in result.sources:
            status = "✅" if s.success else "❌"
            lines.append(f"  {status} {s.provider_name}: {s.market_count} markets ({s.processing_time_ms:.0f}ms, {s.cost_hbar} HBAR)")
        lines.append("")
        lines.append(f"Consensus: {result.consensus.summary}")
        lines.append("")
        if result.analysis:
            lines.append(f"AI Analysis:")
            lines.append(result.analysis)
        return "\n".join(lines)

    @mcp.tool(name="deep_research", description="Perform deep research on a question: searches the web, news, social signals, AND prediction markets. Returns a comprehensive intelligence report with cited sources. This is the premium product — real research, not just API proxying.")
    def deep_research(question: str) -> str:
        from core.ai_analyzer import AIAnalyzer
        from core.deep_research import DeepResearchEngine

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        engine = DeepResearchEngine(settings, provider_registry, AIAnalyzer(settings))
        report = loop.run_until_complete(engine.research(hedera.generate_request_id(), question))
        d = report.to_dict()

        lines = [
            f"=== Deep Research Report ===",
            f"Question: {d['question']}",
            f"Status: {d['status']}",
            f"Processing time: {d['processing_time_ms']:.0f}ms",
            f"",
            f"Sources: {d['sources']['web']} web, {d['sources']['news']} news",
            f"Social sentiment: {d['social_signals'].get('sentiment', 'N/A')}",
            f"",
        ]
        if report.web_results:
            lines.append("Top Web Results:")
            for r in report.web_results[:4]:
                lines.append(f"  • {r.get('title', '')[:80]}")
            lines.append("")
        if report.news_results:
            lines.append("Top News:")
            for r in report.news_results[:3]:
                lines.append(f"  • {r.get('title', '')[:60]} ({r.get('date', '')})")
            lines.append("")
        if report.market_data:
            lines.append("Prediction Market Data:")
            for pid, data in report.market_data.items():
                m = data.get("markets", [])
                if m:
                    q = m[0].get("question", m[0].get("title", "?"))[:50]
                    p = m[0].get("yes_price", "?")
                    lines.append(f"  {data.get('name', pid)}: {q} → {p}")
            lines.append("")
        if d["analysis"]:
            lines.append("AI Analysis:")
            lines.append(d["analysis"])
        return "\n".join(lines)

    @mcp.tool(name="verified_feed", description="Request a verified data feed — aggregates prices from ALL prediction market providers, computes median with confidence intervals (IQR-based), and returns a cryptographically-style verified price point with audit proof. Best product for agents that need reliable, verified market data.")
    def verified_feed(topic: str = "general") -> str:
        from core.verified_feed import VerifiedFeedEngine

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        engine = VerifiedFeedEngine(settings, provider_registry)
        feed = loop.run_until_complete(engine.produce_feed(hedera.generate_request_id(), topic))
        a = feed.aggregate

        lines = [
            f"=== Verified Data Feed ===",
            f"Topic: {feed.topic}",
            f"",
            f"Median Price: {a.price}",
            f"Confidence: {a.confidence:.1%}",
            f"Sources: {a.sources}",
            f"Agreement: {a.agreement:.1%}",
            f"Verification: {feed.verification.upper()}",
            f"Timestamp: {a.timestamp}",
            f"",
            f"Source Breakdown:",
        ]
        for s in feed.sources:
            if s.success:
                lines.append(f"  ✅ {s.provider_name}: price={s.price}, weight={s.weight}")
            else:
                lines.append(f"  ❌ {s.provider_name}: {s.error}")
        lines.extend([
            "",
            f"Cost: {feed.total_cost_hbar} HBAR total",
            f"Processing: {feed.processing_time_ms:.0f}ms",
        ])
        return "\n".join(lines)

    @mcp.tool(name="get_price", description="Get a verified price for any asset from MULTIPLE oracles. Returns JSON with prices, spread, confidence, 24h change, volume.")
    def get_price(asset: str = "BTC/USD") -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        from core.oracle_hub import OracleHub
        hub = OracleHub()
        prices = loop.run_until_complete(hub.get_price(asset.upper()))
        loop.run_until_complete(hub.close())

        if not prices:
            return json.dumps({"asset": asset, "error": "No prices available"})

        vals = [p.price for p in prices]
        spread = max(vals) - min(vals)
        mid = sum(vals) / len(vals)
        spread_pct = (spread / mid) * 100
        conf = "HIGH" if spread_pct < 0.05 else "MEDIUM" if spread_pct < 0.2 else "LOW"

        return json.dumps({
            "asset": asset.upper(),
            "oracles_consulted": len(prices),
            "price_median": round(mid, 6),
            "spread_pct": round(spread_pct, 4),
            "confidence": conf,
            "timestamp": prices[0].timestamp,
            "sources": [p.to_dict() for p in prices],
        }, indent=2)

    @mcp.tool(name="list_assets", description="List all available assets with their oracle sources. 36 assets across crypto, equities, commodities, and forex.")
    def list_assets() -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        from core.oracle_hub import OracleHub, PYTH_FEEDS, BINANCE_SYMBOLS, FOREX_ASSETS
        hub = OracleHub()
        assets = hub.all_assets
        loop.run_until_complete(hub.close())

        equities = {"AAPL/USD","MSFT/USD","NVDA/USD","GOOGL/USD","AMZN/USD","TSLA/USD","META/USD"}
        commodities = {"XAU/USD","XAG/USD"}
        forex = set(FOREX_ASSETS)
        crypto = [a for a in assets if a not in equities and a not in commodities and a not in forex]

        lines = ["=== Available Assets ===", ""]
        lines.append("  Crypto")
        for a in sorted(crypto):
            srcs = []
            if a in PYTH_FEEDS: srcs.append("Pyth")
            if a in BINANCE_SYMBOLS: srcs.append("Binance")
            lines.append(f"    {a:<12} {len(srcs)} oracles: {', '.join(srcs) if srcs else 'CoinGecko+DeFiLlama'}")

        lines.append("")
        lines.append("  Equities")
        for a in sorted(equities):
            lines.append(f"    {a:<12} 1 oracle: Pyth")

        lines.append("")
        lines.append("  Commodities")
        for a in sorted(commodities):
            lines.append(f"    {a:<12} 1 oracle: Pyth")

        lines.append("")
        lines.append("  Forex")
        for a in sorted(forex):
            lines.append(f"    {a:<12} 1 oracle: ForexAPI")

        lines.append("")
        lines.append(f"  Total: {len(assets)} assets across 5 sources")
        return "\n".join(lines)

    @mcp.tool(name="get_asset_profile", description="Get complete profile for an asset: all oracle prices, spread analysis, 24h change, volume, market cap, and confidence score.")
    def get_asset_profile(asset: str = "HBAR/USD") -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        from core.oracle_hub import OracleHub
        hub = OracleHub()
        prices = loop.run_until_complete(hub.get_price(asset.upper()))
        loop.run_until_complete(hub.close())

        if not prices:
            return json.dumps({"asset": asset, "error": "No prices available"})

        vals = [p.price for p in prices]
        spread = max(vals) - min(vals)
        mid = sum(vals) / len(vals)
        spread_pct = (spread / mid) * 100
        conf = "HIGH" if spread_pct < 0.05 else "MEDIUM" if spread_pct < 0.2 else "LOW"

        # Aggregate enriched data
        changes = [p.change_24h for p in prices if p.change_24h is not None]
        volumes = [p.volume_24h for p in prices if p.volume_24h is not None]
        caps = [p.market_cap for p in prices if p.market_cap is not None]

        return json.dumps({
            "asset": asset.upper(),
            "oracles_consulted": len(prices),
            "price_median": round(mid, 6),
            "price_min": round(min(vals), 6),
            "price_max": round(max(vals), 6),
            "spread_pct": round(spread_pct, 4),
            "confidence": conf,
            "timestamp": prices[0].timestamp,
            "change_24h": round(sum(changes) / len(changes), 2) if changes else None,
            "volume_24h": round(sum(volumes), 2) if volumes else None,
            "market_cap": round(sum(caps) / len(caps), 2) if caps else None,
            "sources": [p.to_dict() for p in prices],
        }, indent=2)

    @mcp.tool(name="scan_arbitrage", description="Scan all tracked assets for price discrepancies across oracles. Returns arbitrage opportunities ranked by spread percentage.")
    def scan_arbitrage(min_spread: float = 0.01) -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        from core.oracle_hub import OracleHub
        from core.arbitrage_engine import ArbitrageEngine
        hub = OracleHub()
        engine = ArbitrageEngine(hub)
        signals = loop.run_until_complete(engine.scan_all())
        loop.run_until_complete(hub.close())

        lines = ["=== Arbitrage Scan ===", ""]
        for s in sorted(signals, key=lambda x: x.spread_pct, reverse=True):
            if s.spread_pct >= min_spread:
                lines.append(f"  {s.asset:10s} spread={s.spread_pct:.3f}% [{s.opportunity}]")
                lines.append(f"           {s.analysis}")
                lines.append("")
        if len(lines) == 2:
            lines.append("  No arbitrage opportunities above threshold.")
        return "\n".join(lines)

    # ── Hedera Agent Kit Plugin Tools (Enterprise) ──────────────────────

    _kit_plugin = None

    @mcp.tool(name="kit_setup", description="[Enterprise Plugin] Set up the Hedera Agent Kit in an isolated environment. Run once before using other kit_* tools.")
    def kit_setup() -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from plugins.hedera_kit_bridge import HederaKitPlugin
            _kit_plugin = HederaKitPlugin(
                settings.hedera_operator_id,
                settings.hedera_operator_key,
                settings.hedera_network,
            )
            _kit_plugin.setup()
            _kit_plugin.start()
            mcp._kit_plugin = _kit_plugin
            return "✅ Hedera Agent Kit plugin installed and running in isolated venv."
        except Exception as e:
            return f"❌ Setup failed: {e}"

    @mcp.tool(name="kit_account_balance", description="[Enterprise Plugin] Get HBAR balance of a Hedera account via Hedera Agent Kit.")
    def kit_account_balance(account_id: str = "") -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        plugin = getattr(mcp, "_kit_plugin", None)
        if not plugin or not plugin._ready:
            return "❌ Kit plugin not running. Call kit_setup first."
        try:
            aid = account_id or settings.hedera_operator_id
            result = loop.run_until_complete(plugin.get_account_balance(aid))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"❌ Error: {e}"

    @mcp.tool(name="kit_transfer_hbar", description="[Enterprise Plugin] Transfer HBAR to another account via Hedera Agent Kit. Requires kit_setup first.")
    def kit_transfer_hbar(to: str, amount: int) -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        plugin = getattr(mcp, "_kit_plugin", None)
        if not plugin or not plugin._ready:
            return "❌ Kit plugin not running. Call kit_setup first."
        try:
            result = loop.run_until_complete(plugin.transfer_hbar(to, amount))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"❌ Error: {e}"

    @mcp.tool(name="kit_create_topic", description="[Enterprise Plugin] Create an HCS topic via Hedera Agent Kit. Requires kit_setup first.")
    def kit_create_topic(memo: str = "HashA2A Enterprise Topic") -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        plugin = getattr(mcp, "_kit_plugin", None)
        if not plugin or not plugin._ready:
            return "❌ Kit plugin not running. Call kit_setup first."
        try:
            result = loop.run_until_complete(plugin.create_topic(memo))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"❌ Error: {e}"

    @mcp.tool(name="kit_submit_message", description="[Enterprise Plugin] Submit a message to an HCS topic via Hedera Agent Kit. Requires kit_setup first.")
    def kit_submit_message(topic_id: str, message: str) -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        plugin = getattr(mcp, "_kit_plugin", None)
        if not plugin or not plugin._ready:
            return "❌ Kit plugin not running. Call kit_setup first."
        try:
            result = loop.run_until_complete(plugin.submit_message(topic_id, message))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"❌ Error: {e}"

    @mcp.tool(name="kit_get_account_info", description="[Enterprise Plugin] Get detailed account information via Hedera Agent Kit. Requires kit_setup first.")
    def kit_get_account_info(account_id: str = "") -> str:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        plugin = getattr(mcp, "_kit_plugin", None)
        if not plugin or not plugin._ready:
            return "❌ Kit plugin not running. Call kit_setup first."
        try:
            aid = account_id or settings.hedera_operator_id
            result = loop.run_until_complete(plugin.get_account_info(aid))
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"❌ Error: {e}"

    return mcp
