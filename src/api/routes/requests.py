import time
from fastapi import APIRouter, Depends, HTTPException

from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.provider_registry import ProviderRegistry
from core.agent_registry import AgentRegistry
from core.consensus_logger import ConsensusLogger
from api.deps import (
    get_hedera_manager,
    get_payment_engine,
    get_provider_registry,
    get_agent_registry,
    get_consensus_logger,
)
from models.schemas import (
    QueryRequest,
    PaymentRequest,
    DataResponse,
    RequestStatus,
)

router = APIRouter(prefix="/requests", tags=["requests"])

_inflight: dict[str, DataResponse] = {}


@router.post("", status_code=201)
async def create_request(
    body: QueryRequest,
    hedera: HederaManager = Depends(get_hedera_manager),
    payment_engine: PaymentEngine = Depends(get_payment_engine),
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
):
    provider = provider_registry.get(body.provider_id)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{body.provider_id}' not found. Available: {[p.provider_id for p in provider_registry.list()]}",
        )

    if body.max_cost_hbar is not None and body.max_cost_hbar < provider.cost_hbar:
        raise HTTPException(
            status_code=402,
            detail=f"Provider costs {provider.cost_hbar} HBAR, but max_cost_hbar is {body.max_cost_hbar}",
        )

    request_id = hedera.generate_request_id()
    inbound_topic = await hedera.get_or_create_inbound_topic()

    payment = PaymentRequest(
        request_id=request_id,
        provider_id=provider.provider_id,
        amount_hbar=provider.cost_hbar,
        destination_account=hedera.settings.treasury_account,
        memo=f"HASHA2A:{request_id}:{provider.provider_id}",
        expires_at=int(time.time()) + hedera.settings.payment_ttl_seconds,
    )

    payment_engine.register_request(payment)

    return {
        "request_id": request_id,
        "provider_id": provider.provider_id,
        "provider_name": provider.name,
        "status": RequestStatus.AWAITING_PAYMENT.value,
        "payment": {
            "amount_hbar": payment.amount_hbar,
            "hip991": True,
            "inbound_topic_id": str(inbound_topic),
        },
        "instructions": (
            f"1. Submit a JSON message to HCS topic {inbound_topic} with: "
            f'{{"request_id": "{request_id}", "provider": "{provider.provider_id}", "params": {body.params}}} '
            f"2. HIP-991 will auto-collect {provider.cost_hbar} HBAR from your account "
            f"3. Poll GET /api/v1/requests/{request_id} for the result"
        ),
    }


@router.get("/{request_id}")
async def get_request_result(
    request_id: str,
    payment_engine: PaymentEngine = Depends(get_payment_engine),
):
    completed = _inflight.get(request_id)
    if completed:
        return completed

    pending = payment_engine.get_pending(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Request not found or expired")

    return {
        "request_id": request_id,
        "status": pending.status.value,
    }


async def process_paid_request(
    request_id: str,
    hedera: HederaManager,
    payment_engine: PaymentEngine,
    provider_registry: ProviderRegistry,
    agent_registry: AgentRegistry,
    consensus_logger: ConsensusLogger,
):
    pending = payment_engine.get_pending(request_id)
    if not pending:
        return

    pending.status = RequestStatus.PROCESSING
    provider = provider_registry.get(pending.provider_id)
    if not provider:
        pending.status = RequestStatus.FAILED
        return

    try:
        result = await provider.get_data({
            "request_id": request_id,
        })

        result.proof_tx_id = await consensus_logger.log_response(
            response=result,
            query={"request_id": request_id},
            payment_amount=pending.amount_hbar,
            provider_trust_score=provider.reputation.trust_score,
        )

        result.audit_topic_id = str(await hedera.get_or_create_audit_topic())
        result.status = RequestStatus.COMPLETED

        provider.reputation.total_requests += 1
        provider.reputation.successful_requests += 1
        if result.processing_time_ms:
            provider.reputation.response_time_ms = result.processing_time_ms

        agent_registry.increment_request_count()
        _inflight[request_id] = result
        payment_engine.deregister_request(request_id)

    except Exception as e:
        pending.status = RequestStatus.FAILED
        provider.reputation.total_requests += 1
        _inflight[request_id] = DataResponse(
            request_id=request_id,
            provider_id=pending.provider_id,
            status=RequestStatus.FAILED,
            analysis=f"Processing error: {str(e)}",
        )
