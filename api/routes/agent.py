from fastapi import APIRouter, Depends

from core.agent_registry import AgentRegistry
from core.hedera_manager import HederaManager
from api.deps import get_agent_registry, get_hedera_manager
from models.schemas import AgentProfile

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/profile")
async def get_agent_profile(
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentProfile:
    return await agent_registry.get_profile()


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
