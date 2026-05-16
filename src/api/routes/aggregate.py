import time

from fastapi import APIRouter, Depends, HTTPException

from core.config import Settings
from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.provider_registry import ProviderRegistry
from core.data_aggregator import DataAggregator
from core.ai_analyzer import AIAnalyzer
from api.deps import (
    get_hedera_manager,
    get_payment_engine,
    get_provider_registry,
    get_settings,
)
from models.schemas import AggregateRequest, PaymentRequest, RequestStatus

router = APIRouter(prefix="/requests", tags=["aggregate"])

_aggregate_results: dict[str, dict] = {}


def get_aggregator(
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
    settings: Settings = Depends(get_settings),
) -> DataAggregator:
    analyzer = AIAnalyzer(settings)
    return DataAggregator(provider_registry, analyzer, settings)


@router.post("/aggregate", status_code=201)
async def create_aggregate_request(
    body: AggregateRequest,
    hedera: HederaManager = Depends(get_hedera_manager),
    payment_engine: PaymentEngine = Depends(get_payment_engine),
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
    aggregator: DataAggregator = Depends(get_aggregator),
):
    all_providers = provider_registry.list_all()
    if body.providers:
        targets = [p for p in all_providers if p.provider_id in body.providers]
        if not targets:
            raise HTTPException(status_code=404, detail=f"No providers found matching: {body.providers}")
    else:
        targets = all_providers

    total_cost = sum(p.cost_hbar for p in targets)
    if body.max_cost_hbar is not None and total_cost > body.max_cost_hbar:
        raise HTTPException(
            status_code=402,
            detail=f"Aggregate costs {total_cost} HBAR, but max is {body.max_cost_hbar}",
        )

    request_id = hedera.generate_request_id()
    inbound_topic = await hedera.get_or_create_inbound_topic()

    payment = PaymentRequest(
        request_id=request_id,
        provider_id="aggregated",
        amount_hbar=total_cost,
        destination_account=hedera.settings.treasury_account,
        memo=f"HASHA2A:aggregate:{request_id}:{body.query[:20]}",
        expires_at=int(time.time()) + hedera.settings.payment_ttl_seconds,
    )
    payment_engine.register_request(payment)

    return {
        "request_id": request_id,
        "query": body.query,
        "sources": [p.provider_id for p in targets],
        "status": RequestStatus.AWAITING_PAYMENT.value,
        "payment": {
            "amount_hbar": total_cost,
            "hip991": True,
            "inbound_topic_id": str(inbound_topic),
            "note": f"Fee covers ALL {len(targets)} providers",
        },
        "instructions": (
            f"Send HCS message to topic {inbound_topic} with "
            f'{{"request_id": "{request_id}", "type": "aggregate"}} '
            f"HIP-991 will auto-collect {total_cost} HBAR. "
            f"Then poll GET /api/v1/requests/aggregate/{request_id}"
        ),
    }


@router.get("/aggregate/{request_id}")
async def get_aggregate_result(request_id: str):
    result = _aggregate_results.get(request_id)
    if result:
        return result
    raise HTTPException(status_code=404, detail="Aggregate request not found or expired")


async def process_aggregate_request(
    request_id: str,
    hedera: HederaManager,
    payment_engine: PaymentEngine,
    provider_registry: ProviderRegistry,
    aggregator: DataAggregator,
):
    pending = payment_engine.get_pending(request_id)
    if not pending or pending.provider_id != "aggregated":
        return

    pending.status = RequestStatus.PROCESSING

    try:
        result = await aggregator.aggregate(
            request_id=request_id,
            query="latest markets",
            provider_ids=None,
        )
        result.proof_tx_id = await hedera.publish_consensus_record(
            request_id=request_id,
            provider_id="aggregated",
            query={"query": result.query},
            response=result.data or {},
            analysis=result.analysis,
            provider_trust_score=result.verification_score * 100,
            payment_amount=pending.amount_hbar,
        )
        result.audit_topic_id = str(await hedera.get_or_create_audit_topic())

        _aggregate_results[request_id] = result.model_dump(mode="json")
        payment_engine.deregister_request(request_id)
        pending.status = RequestStatus.COMPLETED

    except Exception as e:
        pending.status = RequestStatus.FAILED
        _aggregate_results[request_id] = {
            "request_id": request_id,
            "query": "aggregate",
            "status": RequestStatus.FAILED.value,
            "error": str(e),
        }
