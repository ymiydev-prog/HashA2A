import time

from fastapi import APIRouter, Depends, HTTPException

from core.config import Settings
from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.provider_registry import ProviderRegistry
from core.ai_analyzer import AIAnalyzer
from core.deep_research import DeepResearchEngine
from api.deps import get_hedera_manager, get_payment_engine, get_provider_registry, get_settings
from models.schemas import PaymentRequest, RequestStatus
from pydantic import BaseModel, Field

router = APIRouter(prefix="/research", tags=["research"])

_research_results: dict[str, dict] = {}
_pending_questions: dict[str, str] = {}


class ResearchRequest(BaseModel):
    question: str = Field(..., description="Research question to investigate")
    max_cost_hbar: float | None = Field(default=None, ge=0.0)


def get_research_engine(
    settings: Settings = Depends(get_settings),
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
) -> DeepResearchEngine:
    analyzer = AIAnalyzer(settings)
    return DeepResearchEngine(settings, provider_registry, analyzer)


@router.post("", status_code=201)
async def create_research(
    body: ResearchRequest,
    hedera: HederaManager = Depends(get_hedera_manager),
    payment_engine: PaymentEngine = Depends(get_payment_engine),
    research_engine: DeepResearchEngine = Depends(get_research_engine),
):
    cost_hbar = 1.0
    if body.max_cost_hbar is not None and cost_hbar > body.max_cost_hbar:
        raise HTTPException(status_code=402, detail=f"Research costs {cost_hbar} HBAR")

    request_id = hedera.generate_request_id()
    inbound_topic = await hedera.get_or_create_inbound_topic()

    payment = PaymentRequest(
        request_id=request_id,
        provider_id="research",
        amount_hbar=cost_hbar,
        destination_account=hedera.settings.treasury_account,
        memo=f"HASHA2A:research:{request_id}",
        expires_at=int(time.time()) + hedera.settings.payment_ttl_seconds,
    )
    payment_engine.register_request(payment)
    _pending_questions[request_id] = body.question

    return {
        "request_id": request_id,
        "question": body.question,
        "status": RequestStatus.AWAITING_PAYMENT.value,
        "cost_hbar": cost_hbar,
        "payment": {
            "amount_hbar": cost_hbar,
            "hip991": True,
            "inbound_topic_id": str(inbound_topic),
            "note": "Includes web research, news analysis, social sentiment, and prediction market comparison",
        },
        "instructions": (
            f'Send HCS message to {inbound_topic} with {{"request_id": "{request_id}", "type": "research"}} '
            f"HIP-991 collects {cost_hbar} HBAR. Then poll GET /api/v1/research/{request_id}"
        ),
    }


@router.get("/{request_id}")
async def get_research_result(request_id: str):
    result = _research_results.get(request_id)
    if result:
        return result
    raise HTTPException(status_code=404, detail="Research request not found or expired")


async def process_research_request(
    request_id: str,
    hedera: HederaManager,
    payment_engine: PaymentEngine,
    provider_registry: ProviderRegistry,
    research_engine: DeepResearchEngine,
):
    pending = payment_engine.get_pending(request_id)
    if not pending or pending.provider_id != "research":
        return

    pending.status = RequestStatus.PROCESSING
    try:
        question = _pending_questions.pop(request_id, "general inquiry")
        report = await research_engine.research(request_id, question)
        report.proof_tx_id = await hedera.publish_consensus_record(
            request_id=request_id, provider_id="research",
            query={"question": report.question},
            response={"analysis": report.analysis or ""},
            analysis=report.analysis,
            provider_trust_score=85.0,
            payment_amount=pending.amount_hbar,
        )
        report.audit_topic_id = str(await hedera.get_or_create_audit_topic())
        _research_results[request_id] = report.to_dict()
        payment_engine.deregister_request(request_id)
        pending.status = RequestStatus.COMPLETED
    except Exception as e:
        pending.status = RequestStatus.FAILED
        _research_results[request_id] = {
            "request_id": request_id, "status": RequestStatus.FAILED.value, "error": str(e),
        }
