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
    provider_registry.register(PolymarketEdgeProvider())
    provider_registry.register(KalshiBettingProvider())
    provider_registry.discover()

    mcp = FastMCP(
        name="HashA2A",
        instructions=(
            "A decentralized data oracle where AI agents buy processed intelligence "
            "via HBAR micropayments on Hedera. "
            "Available providers: polymarket (0.5 HBAR) and kalshi (0.3 HBAR)."
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
            return f"Error: Provider '{provider_id}' not found. Available: {[p.provider_id for p in provider_registry.list()]}"

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
            "staked_hbar": sum(p.reputation.staked_hbar for p in provider_registry.list()),
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

    return mcp
