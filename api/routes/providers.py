from fastapi import APIRouter, Depends

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
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_id}' not found",
        )
    return provider.capability
