from fastapi import APIRouter, Depends, HTTPException

from core.staking import StakingManager
from core.provider_registry import ProviderRegistry
from api.deps import get_provider_registry

router = APIRouter(prefix="/staking", tags=["staking"])

_staking_manager = StakingManager()


@router.post("/{provider_id}/slash")
async def slash_provider(
    provider_id: str,
    body: dict,
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
):
    provider = provider_registry.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    reason = body.get("reason", "Quality violation")
    severity = body.get("severity", "low")

    event = _staking_manager.slash_provider(provider, reason, severity)

    return {
        "status": "slashed",
        "event": event.model_dump(),
        "new_staked_hbar": provider.reputation.staked_hbar,
        "new_trust_score": round(provider.reputation.trust_score, 2),
        "risk_level": _staking_manager.get_provider_risk_level(provider),
    }


@router.get("/history")
async def get_slash_history(
    provider_id: str | None = None,
):
    history = _staking_manager.get_slash_history(provider_id)
    return {
        "total_events": len(history),
        "events": [e.model_dump() for e in history],
    }


@router.get("/{provider_id}/risk")
async def get_provider_risk(
    provider_id: str,
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
):
    provider = provider_registry.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    return {
        "provider_id": provider_id,
        "risk_level": _staking_manager.get_provider_risk_level(provider),
        "staked_hbar": provider.reputation.staked_hbar,
        "trust_score": round(provider.reputation.trust_score, 2),
        "slash_history": len(_staking_manager.get_slash_history(provider_id)),
    }
