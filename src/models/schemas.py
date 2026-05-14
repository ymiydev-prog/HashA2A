from pydantic import BaseModel, Field
from typing import Any
from enum import Enum


class RequestStatus(str, Enum):
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"


class PaymentRequest(BaseModel):
    request_id: str
    provider_id: str
    amount_hbar: float
    destination_account: str
    memo: str
    expires_at: int
    status: RequestStatus = RequestStatus.AWAITING_PAYMENT


class QueryRequest(BaseModel):
    provider_id: str = Field(..., description="DataProvider ID, e.g. 'polymarket'")
    params: dict[str, Any] = Field(default_factory=dict, description="Provider-specific parameters")
    quality_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    max_cost_hbar: float | None = Field(default=None, ge=0.0)


class DataResponse(BaseModel):
    request_id: str
    provider_id: str
    status: RequestStatus
    data: dict[str, Any] | None = None
    analysis: str | None = None
    quality_score: float | None = None
    quality_reason: str | None = None
    raw_size_bytes: int | None = None
    proof_tx_id: str | None = None
    audit_topic_id: str | None = None
    processing_time_ms: float | None = None
    provider_trust_score: float | None = None


class ProviderCapability(BaseModel):
    provider_id: str
    name: str
    description: str
    cost_hbar: float
    parameters_schema: dict[str, Any]
    trust_score: float = 50.0
    total_requests: int = 0
    success_rate: float = 1.0
    avg_response_time_ms: float | None = None
    staked_hbar: float = 0.0


class AgentProfile(BaseModel):
    agent_name: str
    agent_version: str
    description: str
    tags: list[str]
    hol_registry_topic: str | None = None
    inbound_topic: str | None = None
    outbound_topic: str | None = None
    treasury_account: str
    supported_providers: list[ProviderCapability]
    uptime_pct: float = 100.0
    total_requests_served: int = 0
    last_broadcast: str | None = None


class DataQualityReport(BaseModel):
    request_id: str
    provider_id: str
    passed: bool
    score: float = 0.0
    reason: str | None = None


class ProviderReputation(BaseModel):
    provider_id: str
    accuracy_score: float = 50.0
    response_time_ms: float | None = None
    uptime_pct: float = 100.0
    dispute_rate: float = 0.0
    staked_hbar: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0

    @property
    def trust_score(self) -> float:
        return (
            0.35 * self.accuracy_score +
            0.20 * (100 - min((self.response_time_ms or 5000) / 100, 100)) +
            0.15 * self.uptime_pct +
            0.10 * (100 - self.dispute_rate * 100) +
            0.20 * min(self.staked_hbar / 10000 * 100, 100)
        )


class ConsensusRecord(BaseModel):
    request_id: str
    provider_id: str
    client_agent_id: str | None = None
    query_hash: str
    response_hash: str
    analysis_hash: str | None = None
    quality_score: float | None = None
    payment_amount: float
    payment_tx_id: str | None = None
    provider_trust_score: float
    timestamp: str
    hcs_message_sequence: int | None = None
