import time
from fastapi import APIRouter, Depends, HTTPException

from core.auction import AuctionManager
from core.provider_registry import ProviderRegistry
from api.deps import get_auction_manager, get_provider_registry

router = APIRouter(prefix="/auctions", tags=["auctions"])


@router.post("/create")
async def create_auction(
    body: dict,
    auction_manager: AuctionManager = Depends(get_auction_manager),
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
):
    request_id = body.get("request_id", f"auction-{int(time.time())}")
    query = body.get("query", {})

    providers = provider_registry.list_all()
    if not providers:
        raise HTTPException(status_code=404, detail="No providers available")

    auction = await auction_manager.create_auction(request_id, query, providers)

    return {
        "request_id": request_id,
        "status": auction.status,
        "total_bids": len(auction.bids),
        "winner": auction.bids[0].model_dump() if auction.bids else None,
        "ranking": [b.model_dump() for b in auction.get_ranking()],
    }


@router.get("/{request_id}")
async def get_auction(
    request_id: str,
    auction_manager: AuctionManager = Depends(get_auction_manager),
):
    auction = auction_manager.get_auction(request_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    return {
        "request_id": request_id,
        "status": auction.status,
        "total_bids": len(auction.bids),
        "winner": auction.bids[0].model_dump() if auction.bids else None,
        "ranking": [b.model_dump() for b in auction.get_ranking()],
    }
