import time
import asyncio
from typing import Any
from pydantic import BaseModel, Field

from core.base_provider import BaseDataProvider
from models.schemas import DataResponse, RequestStatus


class AuctionBid(BaseModel):
    provider_id: str
    cost_hbar: float
    trust_score: float
    estimated_time_ms: float | None = None
    bid_score: float = 0.0


class ReverseAuction:
    """
    Sistema de subastas inversas entre proveedores.
    Cuando un cliente hace una request, múltiples proveedores pujan
    ofreciendo el mejor precio + calidad.
    """

    def __init__(self, request_id: str, query: dict[str, Any]):
        self.request_id = request_id
        self.query = query
        self.bids: list[AuctionBid] = []
        self.created_at = time.monotonic()
        self.status = "open"

    def add_bid(self, bid: AuctionBid):
        self.bids.append(bid)

    def compute_bid_score(self, bid: AuctionBid) -> float:
        cost_weight = 0.4
        trust_weight = 0.4
        speed_weight = 0.2

        cost_score = max(0, 1 - (bid.cost_hbar / 1.0))
        trust_score = bid.trust_score / 100.0
        speed_score = 0.5
        if bid.estimated_time_ms is not None:
            speed_score = max(0, 1 - (bid.estimated_time_ms / 5000))

        return (
            cost_weight * cost_score +
            trust_weight * trust_score +
            speed_weight * speed_score
        )

    def select_winner(self) -> AuctionBid | None:
        if not self.bids:
            return None

        for bid in self.bids:
            bid.bid_score = self.compute_bid_score(bid)

        self.bids.sort(key=lambda b: b.bid_score, reverse=True)
        self.status = "closed"
        return self.bids[0]

    def get_ranking(self) -> list[AuctionBid]:
        for bid in self.bids:
            if bid.bid_score == 0:
                bid.bid_score = self.compute_bid_score(bid)
        return sorted(self.bids, key=lambda b: b.bid_score, reverse=True)


class AuctionManager:
    """
    Gestiona subastas inversas para requests entrantes.
    Coordina la recolección de bids y selección del ganador.
    """

    def __init__(self):
        self._auctions: dict[str, ReverseAuction] = {}
        self._bid_timeout = 5.0

    async def create_auction(
        self,
        request_id: str,
        query: dict[str, Any],
        providers: list[BaseDataProvider],
    ) -> ReverseAuction:
        auction = ReverseAuction(request_id, query)
        self._auctions[request_id] = auction

        bid_tasks = []
        for provider in providers:
            task = asyncio.create_task(
                self._collect_bid(provider, auction, query)
            )
            bid_tasks.append(task)

        try:
            await asyncio.wait_for(
                asyncio.gather(*bid_tasks, return_exceptions=True),
                timeout=self._bid_timeout,
            )
        except asyncio.TimeoutError:
            pass

        winner = auction.select_winner()
        return auction

    async def _collect_bid(
        self,
        provider: BaseDataProvider,
        auction: ReverseAuction,
        query: dict[str, Any],
    ):
        try:
            start = time.monotonic()
            test_result = await provider.get_data({
                "request_id": f"bid-{auction.request_id}",
                **query,
                "limit": 1,
            })
            elapsed = (time.monotonic() - start) * 1000

            bid = AuctionBid(
                provider_id=provider.provider_id,
                cost_hbar=provider.cost_hbar,
                trust_score=provider.reputation.trust_score,
                estimated_time_ms=elapsed,
            )
            auction.add_bid(bid)
        except Exception:
            bid = AuctionBid(
                provider_id=provider.provider_id,
                cost_hbar=provider.cost_hbar,
                trust_score=provider.reputation.trust_score,
                estimated_time_ms=None,
            )
            auction.add_bid(bid)

    def get_auction(self, request_id: str) -> ReverseAuction | None:
        return self._auctions.get(request_id)

    def cleanup_expired(self, max_age: float = 300.0):
        now = time.monotonic()
        expired = [
            rid for rid, auction in self._auctions.items()
            if (now - auction.created_at) > max_age
        ]
        for rid in expired:
            del self._auctions[rid]
