from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any
from enum import Enum
import uuid
import time


class TaskStatus(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PartType(str, Enum):
    TEXT = "text"
    DATA = "data"
    FILE = "file"


class MessagePart(BaseModel):
    type: PartType
    text: str | None = None
    data: dict[str, Any] | None = None
    file_uri: str | None = None
    metadata: dict[str, Any] | None = None


class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    parts: list[MessagePart]
    metadata: dict[str, Any] | None = None
    created_at: int = Field(default_factory=lambda: int(time.time()))


class TaskObject(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "hasha2a"
    status: TaskStatus = TaskStatus.SUBMITTED
    parts: list[MessagePart] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list, description="List of artifact IDs")
    metadata: dict[str, Any] | None = None
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    context_id: str | None = None

    def transition(self, new_status: TaskStatus) -> None:
        self.status = new_status
        self.updated_at = int(time.time())

    def add_part(self, part: MessagePart) -> None:
        self.parts.append(part)
        self.updated_at = int(time.time())

    def add_artifact_id(self, artifact_id: str) -> None:
        if artifact_id not in self.artifacts:
            self.artifacts.append(artifact_id)
        self.updated_at = int(time.time())

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("task_id must be at least 8 characters")
        return v


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
    amount_hbar: float = Field(default=0.0, ge=0.0, description="Payment amount in HBAR")
    destination_account: str
    memo: str
    expires_at: int = Field(default=0, ge=0, description="Unix timestamp when payment expires")
    status: RequestStatus = RequestStatus.AWAITING_PAYMENT

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("request_id must be at least 8 characters")
        return v

    @field_validator("destination_account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        if v and not v.startswith("0.0.") and not v.startswith("0x"):
            raise ValueError("destination_account must start with 0.0. (Hedera) or 0x (EVM)")
        return v


class QueryRequest(BaseModel):
    provider_id: str = Field(..., description="DataProvider ID, e.g. 'polymarket'")
    params: dict[str, Any] = Field(default_factory=dict, description="Provider-specific parameters")
    quality_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    max_cost_hbar: float | None = Field(default=None, ge=0.0)

    @field_validator("provider_id")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"polymarket", "kalshi", "predictit", "manifold", "aggregated", "research", "feed"}
        if v and v not in allowed:
            from warnings import warn
            warn(f"Unknown provider '{v}'. Known: {allowed}")
        return v


class DataResponse(BaseModel):
    request_id: str
    provider_id: str
    status: RequestStatus
    data: dict[str, Any] | None = None
    analysis: str | None = None
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
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
    started_at: str | None = None
    avg_response_time_ms: float | None = None
    active_connections: int = 0


class AgentHealthCheck(BaseModel):
    status: str = "healthy"
    uptime_seconds: float = 0
    started_at: str
    version: str
    providers_count: int
    total_requests_served: int
    avg_response_time_ms: float | None = None
    last_request_at: str | None = None
    hedera_connected: bool = False
    mirror_node_reachable: bool = False
    agents_discovered: int = 0
    online_agents: int = 0


class AgentDiscoveryEntry(BaseModel):
    agent_name: str
    agent_id: str
    description: str
    tags: list[str]
    inbound_topic: str | None = None
    outbound_topic: str | None = None
    treasury_account: str
    supported_chains: list[str]
    fees: dict[str, Any]
    trust_score: float = 50.0
    total_requests: int = 0
    last_seen: str
    registered_at: str | None = None


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


class FeedRequest(BaseModel):
    topic: str = Field(..., description="Topic/asset to get verified data for, e.g. 'BTC price', 'election 2028'")
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum confidence interval (0-1)")
    max_cost_hbar: float | None = Field(default=None, ge=0.0)


class AggregateRequest(BaseModel):
    query: str = Field(..., description="Query/topic to aggregate across providers")
    providers: list[str] | None = Field(default=None, description="Provider IDs to query, or null for all")
    max_cost_hbar: float | None = Field(default=None, ge=0.0)
    quality_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class SourceResult(BaseModel):
    provider_id: str
    provider_name: str
    success: bool
    market_count: int = 0
    cost_hbar: float = 0
    processing_time_ms: float | None = None
    error: str | None = None


class ConsensusReport(BaseModel):
    agreement_score: float = 0.0
    total_sources: int = 0
    successful_sources: int = 0
    summary: str | None = None


class AggregatedResult(BaseModel):
    request_id: str
    query: str
    sources: list[SourceResult]
    consensus: ConsensusReport
    data: dict[str, Any] | None = None
    analysis: str | None = None
    verification_score: float = 0.0
    total_cost_hbar: float = 0
    proof_tx_id: str | None = None
    audit_topic_id: str | None = None
    processing_time_ms: float | None = None


class VerifiedPricePoint(BaseModel):
    asset: str
    price: float
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    bid: float | None = None
    ask: float | None = None
    sources: int = Field(default=0, ge=0)
    agreement: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: int = Field(default=0, ge=0)

    @field_validator("asset")
    @classmethod
    def asset_uppercase(cls, v: str) -> str:
        return v.upper()


class SourceFeedBack(BaseModel):
    provider_id: str
    provider_name: str
    price: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    success: bool = False
    error: str | None = None


class VerifiedDataFeed(BaseModel):
    feed_id: str
    topic: str
    aggregate: VerifiedPricePoint
    sources: list[SourceFeedBack]
    verification: str = Field(default="low", pattern=r"^(high|medium|low)$")
    total_cost_hbar: float = 0.0
    proof_tx_id: str | None = None
    audit_topic_id: str | None = None
    processing_time_ms: float | None = None


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
