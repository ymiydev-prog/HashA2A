from fastapi import APIRouter, Depends, Query, HTTPException

from core.agent_registry import AgentRegistry
from core.hedera_manager import HederaManager
from core.agent_directory import agent_directory
from core.agent_messaging import agent_messaging
from core.protocols.handshake import handshake_manager
from api.deps import get_agent_registry, get_hedera_manager
from models.schemas import AgentProfile, AgentHealthCheck, AgentDiscoveryEntry

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/profile")
async def get_agent_profile(
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentProfile:
    return await agent_registry.get_profile()


@router.get("/health")
async def get_health_check(
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentHealthCheck:
    return agent_registry.get_health_check()


@router.post("/broadcast")
async def broadcast_presence(
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    tx_id = await agent_registry.broadcast_presence()
    if tx_id:
        return {"status": "broadcasted", "transaction_id": tx_id}
    return {"status": "failed", "detail": "Broadcast failed - check network connection"}


@router.post("/register-hol")
async def register_in_hol(
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    tx_id = await agent_registry.register_in_hol()
    if tx_id:
        return {
            "status": "registered",
            "transaction_id": tx_id,
            "detail": "HashA2A is now discoverable in the HOL global registry",
        }
    return {"status": "failed", "detail": "Registration failed - check HOL topic ID and network"}


@router.get("/topics")
async def get_topics(
    hedera: HederaManager = Depends(get_hedera_manager),
):
    return {
        "inbound_topic": str(await hedera.get_or_create_inbound_topic()),
        "outbound_topic": str(await hedera.get_or_create_outbound_topic()),
        "audit_topic": str(await hedera.get_or_create_audit_topic()),
        "network": hedera.settings.hedera_network,
    }


@router.get("/discovery")
async def discover_agents(
    tag: str | None = Query(None, description="Filter agents by tag"),
    chain: str | None = Query(None, description="Filter by supported chain"),
    min_trust: float | None = Query(None, ge=0, le=100, description="Minimum trust score"),
    presence: str | None = Query(None, description="Filter by presence: online, offline"),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Discover agents in the Hedera ecosystem.
    Returns agents from the AgentDirectory (discovered via HOL Registry)
    plus the current agent itself.
    """
    agents = agent_registry.get_discovered_agents(
        tag=tag, chain=chain, min_trust=min_trust,
    )

    if presence:
        agents = [a for a in agents if a.presence == presence]

    entries = []
    for agent in agents:
        entries.append(AgentDiscoveryEntry(
            agent_name=agent.agent_name,
            agent_id=agent.agent_id,
            description=agent.description,
            tags=agent.tags,
            inbound_topic=agent.inbound_topic,
            outbound_topic=agent.outbound_topic,
            treasury_account=agent.treasury_account,
            supported_chains=agent.supported_chains,
            fees=agent.fees,
            trust_score=agent.trust_score,
            total_requests=agent.total_requests,
            last_seen=agent.last_seen,
            registered_at=agent.registered_at,
        ))

    return entries


@router.post("/handshake/{agent_id}")
async def initiate_handshake(
    agent_id: str,
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """Initiate a handshake with another agent."""
    result = await agent_registry.initiate_handshake(agent_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/connections")
async def get_connections():
    """List all agent connections and their states."""
    return {
        "connections": handshake_manager.list_connections(),
        "total": len(handshake_manager.list_connections()),
    }


@router.post("/message/{agent_id}")
async def send_message(
    agent_id: str,
    body: dict,
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """Send a direct message to another agent."""
    action = body.get("action", "ping")
    payload = body.get("payload", {})

    result = await agent_registry.send_message_to_agent(agent_id, action, payload)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/messages")
async def get_messages(limit: int = Query(50, le=200)):
    """Get message log."""
    if agent_messaging is None:
        return {"messages": []}
    return {
        "messages": agent_messaging.get_message_log(limit),
        "stats": agent_messaging.get_stats(),
    }


@router.get("/directory/stats")
async def get_directory_stats():
    """Get agent directory statistics."""
    return agent_directory.get_stats()
