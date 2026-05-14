from fastapi import APIRouter, Depends, HTTPException

from core.provider_registry import ProviderRegistry
from api.deps import get_provider_registry
from models.schemas import ProviderCapability

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers(
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
) -> list[ProviderCapability]:
    return provider_registry.list_capabilities()


@router.get("/{provider_id}")
async def get_provider(
    provider_id: str,
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
) -> ProviderCapability:
    provider = provider_registry.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    return provider.capability


@router.post("/{provider_id}/stake")
async def stake_provider(
    provider_id: str,
    body: dict,
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
):
    amount = body.get("amount_hbar", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount_hbar must be positive")

    if provider_registry.stake(provider_id, amount):
        provider = provider_registry.get(provider_id)
        return {
            "status": "staked",
            "provider_id": provider_id,
            "total_staked": provider.reputation.staked_hbar,
            "new_trust_score": round(provider.reputation.trust_score, 2),
        }
    raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")


@router.post("/{provider_id}/unstake")
async def unstake_provider(
    provider_id: str,
    body: dict,
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
):
    amount = body.get("amount_hbar", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount_hbar must be positive")

    if provider_registry.unstake(provider_id, amount):
        provider = provider_registry.get(provider_id)
        return {
            "status": "unstaked",
            "provider_id": provider_id,
            "total_staked": provider.reputation.staked_hbar,
            "new_trust_score": round(provider.reputation.trust_score, 2),
        }
    raise HTTPException(status_code=400, detail="Insufficient staked balance or provider not found")
