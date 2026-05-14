from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import Settings
from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.agent_registry import AgentRegistry
from core.provider_registry import ProviderRegistry
from core.consensus_logger import ConsensusLogger
from api.routes import requests, providers, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    hedera = HederaManager(settings)
    provider_registry = ProviderRegistry()
    payment_engine = PaymentEngine(settings, hedera)
    consensus_logger = ConsensusLogger(hedera)
    agent_registry = AgentRegistry(settings, hedera, provider_registry)

    from providers.polymarket_edge import PolymarketEdgeProvider
    from providers.kalshi import KalshiBettingProvider
    provider_registry.register(PolymarketEdgeProvider())
    provider_registry.register(KalshiBettingProvider())

    discovered = provider_registry.discover()
    if discovered:
        print(f"Auto-discovered providers: {discovered}")

    app.state.settings = settings
    app.state.hedera = hedera
    app.state.provider_registry = provider_registry
    app.state.payment_engine = payment_engine
    app.state.consensus_logger = consensus_logger
    app.state.agent_registry = agent_registry

    async def on_payment(request_id: str):
        await requests.process_paid_request(
            request_id=request_id,
            hedera=hedera,
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
        inbound = await hedera.get_or_create_inbound_topic()
        hedera_ok = True
    except Exception as e:
        broadcast_task = None
        print(f"⚠️  Hedera not configured: {e}")
        print(f"   Create .env with credentials or run with mock data")

    print(f"\nHashA2A v{settings.agent_version} running on {settings.api_host}:{settings.api_port}")
    print(f"Providers: {[p.provider_id for p in provider_registry.list_all()]}")
    print(f"MCP:   http://localhost:{settings.api_port}/mcp")
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
        title="HashA2A — The Agent-to-Agent Intelligence Layer",
        description=(
            "A modular data oracle where AI agents buy processed intelligence "
            "via HBAR micropayments on Hedera. "
            "Uses HIP-991 Custom Fees for automatic payment collection."
        ),
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(requests.router, prefix="/api/v1")
    app.include_router(providers.router, prefix="/api/v1")
    app.include_router(agent.router, prefix="/api/v1")

    from mcp_server import create_mcp_server
    mcp = create_mcp_server()
    app.mount("/mcp", mcp.streamable_http_app())

    return app


app = create_app()
