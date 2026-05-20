import json
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import Settings
from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.agent_registry import AgentRegistry
from core.provider_registry import ProviderRegistry
from core.consensus_logger import ConsensusLogger
from core.auction import AuctionManager
from api.routes import requests, providers, agent, dashboard, auctions, staking, websocket, aggregate, research, tasks, auth, a2a_rpc


async def _run_twitter_scheduler(scheduler, agent_registry, provider_registry):
    """Periodically check schedule and post tweets."""
    import asyncio
    while True:
        try:
            total_tasks = getattr(agent_registry, "_total_requests_served", 0)
            providers = len(provider_registry.list_all()) if provider_registry else 0
            oracles = 3
            await scheduler.run_scheduled(total_tasks, providers, oracles)
        except Exception:
            pass
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    hedera = HederaManager(settings)
    provider_registry = ProviderRegistry()
    payment_engine = PaymentEngine(settings, hedera)
    consensus_logger = ConsensusLogger(hedera)
    agent_registry = AgentRegistry(settings, hedera, provider_registry)
    auction_manager = AuctionManager()

    from providers.polymarket_edge import PolymarketEdgeProvider
    from providers.kalshi import KalshiBettingProvider
    from providers.predictit import PredictItProvider
    from providers.manifold import ManifoldMarketsProvider
    provider_registry.register(PolymarketEdgeProvider())
    provider_registry.register(KalshiBettingProvider())
    provider_registry.register(PredictItProvider())
    provider_registry.register(ManifoldMarketsProvider())

    discovered = provider_registry.discover()
    if discovered:
        print(f"Auto-discovered providers: {discovered}")

    app.state.settings = settings
    app.state.hedera = hedera
    app.state.provider_registry = provider_registry
    app.state.payment_engine = payment_engine
    app.state.consensus_logger = consensus_logger
    app.state.agent_registry = agent_registry
    app.state.auction_manager = auction_manager

    from core.ai_analyzer import AIAnalyzer
    from core.data_aggregator import DataAggregator
    from core.deep_research import DeepResearchEngine
    ai_analyzer = AIAnalyzer(settings)
    data_aggregator = DataAggregator(provider_registry, ai_analyzer, settings)
    app.state.data_aggregator = data_aggregator
    research_engine = DeepResearchEngine(settings, provider_registry, ai_analyzer)
    app.state.research_engine = research_engine

    from core.twitter_promoter import ContentScheduler
    twitter_scheduler = ContentScheduler(
        api_key=settings.twitter_api_key,
        api_secret=settings.twitter_api_secret,
        access_token=settings.twitter_access_token,
        access_secret=settings.twitter_access_secret,
        enabled=settings.twitter_enabled,
    )
    app.state.twitter_scheduler = twitter_scheduler
    if twitter_scheduler.enabled:
        print(f"🐦 Twitter auto-promotion enabled (@hasha2a)")

    async def on_payment(request_id: str):
        pending = payment_engine.get_pending(request_id)
        if not pending:
            return
        if pending.provider_id == "aggregated":
            await aggregate.process_aggregate_request(
                request_id=request_id, hedera=hedera,
                payment_engine=payment_engine,
                provider_registry=provider_registry,
                aggregator=data_aggregator,
            )
        elif pending.provider_id == "research":
            await research.process_research_request(
                request_id=request_id, hedera=hedera,
                payment_engine=payment_engine,
                provider_registry=provider_registry,
                research_engine=research_engine,
            )
        else:
            await requests.process_paid_request(
                request_id=request_id, hedera=hedera,
                payment_engine=payment_engine,
                provider_registry=provider_registry,
                agent_registry=agent_registry,
                consensus_logger=consensus_logger,
            )

    payment_engine.on_payment_confirmed(on_payment)

    import asyncio
    hedera_ok = False
    try:
        await payment_engine.start()
        broadcast_task = asyncio.create_task(agent_registry.run_periodic_broadcast())
        twitter_task = asyncio.create_task(_run_twitter_scheduler(twitter_scheduler, agent_registry, provider_registry))
        inbound = await hedera.get_or_create_inbound_topic()
        hedera_ok = True
    except Exception as e:
        broadcast_task = None
        twitter_task = None
        print(f"⚠️  Hedera not configured: {e}")
        print(f"   Create .env with credentials or run with mock data")

    # Initialize MCP session manager
    from mcp_server import create_mcp_server
    mcp = create_mcp_server()
    mcp.settings.streamable_http_path = "/"
    mcp_app = mcp.streamable_http_app()
    app.state.mcp_app = mcp_app

    mcp_session_mgr = mcp._session_manager
    if mcp_session_mgr:
        async with mcp_session_mgr.run():
            print(f"\nHashA2A v{settings.agent_version} running on {settings.api_host}:{settings.api_port}")
            print(f"Providers: {[p.provider_id for p in provider_registry.list_all()]}")
            print(f"MCP:   http://localhost:{settings.api_port}/mcp")
            print(f"Dashboard: http://localhost:{settings.api_port}/dashboard")
            if hedera_ok:
                print(f"HIP-991: {inbound} | {settings.hip991_fee_hbar} HBAR fee")
            print("")

            yield
    else:
        print(f"\nHashA2A v{settings.agent_version} running on {settings.api_host}:{settings.api_port}")
        print(f"Providers: {[p.provider_id for p in provider_registry.list_all()]}")
        print(f"MCP:   http://localhost:{settings.api_port}/mcp")
        print(f"Dashboard: http://localhost:{settings.api_port}/dashboard")
        if hedera_ok:
            print(f"HIP-991: {inbound} | {settings.hip991_fee_hbar} HBAR fee")
        print("")

        yield

    if broadcast_task:
        broadcast_task.cancel()
    try:
        hedera.close()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="HashA2A — Agent-to-Agent Intelligence Layer",
        description=(
            "A decentralized data marketplace where AI agents buy verified "
            "multi-oracle intelligence via HBAR (HIP-991) or USDC (x402/AP2).\n\n"
            "## Capabilities\n"
            "- **OracleHub**: Multi-oracle prices (Pyth, CoinGecko, Chainlink)\n"
            "- **Arbitrage Engine**: Cross-oracle spread detection\n"
            "- **A2A Protocol**: Google A2A compliant, JSON-RPC 2.0, SSE streaming\n"
            "- **Deep Research**: Web search + AI analysis (OpenAI web_search)\n"
            "- **MCP Server**: 10 tools for Claude/Cursor/LangChain\n"
            "- **Auth**: Ephemeral JWT tokens + AP2 mandates\n\n"
            "## Payment\n"
            "USDC prices are fixed. HBAR prices update in real-time from CoinGecko.\n\n"
            "## Agent Discovery\n"
            "`/.well-known/agent.json` · `/llms.txt` · `/mcp/`\n\n"
            "## Links\n"
            "[GitHub](https://github.com/ymiydev-prog/HashA2A) · "
            "[Dashboard](/dashboard) · "
            "[Oracle Dashboard](/dashboard/oracles) · "
            "[Task Dashboard](/dashboard/tasks) · "
            "[X](https://x.com/hasha2a)"
        ),
        version="0.2.0",
        lifespan=lifespan,
        contact={
            "name": "HashA2A",
            "url": "https://github.com/ymiydev-prog/HashA2A",
        },
        license_info={
            "name": "MIT",
            "url": "https://github.com/ymiydev-prog/HashA2A/blob/main/LICENSE",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)[:200], "type": type(exc).__name__},
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "path": str(request.url.path)},
        )

    app.include_router(requests.router, prefix="/api/v1")
    app.include_router(providers.router, prefix="/api/v1")
    app.include_router(agent.router, prefix="/api/v1")
    app.include_router(auctions.router, prefix="/api/v1")
    app.include_router(staking.router, prefix="/api/v1")
    app.include_router(websocket.router)
    app.include_router(dashboard.router)
    app.include_router(aggregate.router)
    app.include_router(research.router)
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(a2a_rpc.router, prefix="/api/v1")
    from api.routes.feeds import router as feeds_router
    app.include_router(feeds_router, prefix="/api/v1")

    async def mcp_asgi(scope, receive, send):
        if scope["type"] != "http":
            return

        if scope["method"] == "GET":
            resp = JSONResponse({
                "name": "HashA2A MCP Server",
                "protocol": "MCP Streamable HTTP",
                "version": "0.2.0",
                "tools": [
                    "list_providers", "get_market_data", "check_request",
                    "get_agent_profile", "analyze_market", "deep_research",
                    "aggregate_market_data", "verified_feed", "get_price",
                    "scan_arbitrage", "list_assets", "get_asset_profile",
                    "kit_setup", "kit_account_balance", "kit_transfer_hbar",
                    "kit_create_topic", "kit_submit_message", "kit_get_account_info",
                ],
                "pricing": {
                    "free": "all tools (incl. enterprise plugin)",
                    "paid": "get_market_data (0.5 HBAR), deep_research (1 HBAR), get_price ($0.25 USDC), scan_arbitrage ($0.50 USDC)",
                },
                "discovery": {
                    "a2a_agent_card": "/.well-known/agent.json",
                    "x402_manifest": "/.well-known/x402.json",
                    "llms_txt": "/llms.txt",
                },
                "example": {
                    "jsonrpc": "2.0", "id": 1,
                    "method": "tools/list", "params": {},
                },
            })
            await resp(scope, receive, send)
        else:
            mcp_app = app.state.mcp_app
            await mcp_app(scope, receive, send)

    app.mount("/mcp/", mcp_asgi)

    import os
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app

app = create_app()
