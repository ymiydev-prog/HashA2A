from abc import ABC, abstractmethod
from typing import ClassVar, Any
from models.schemas import DataResponse, ProviderReputation, DataQualityReport, RequestStatus


class BaseDataProvider(ABC):
    provider_id: ClassVar[str]
    name: ClassVar[str]
    description: ClassVar[str]
    cost_hbar: ClassVar[float]
    parameters_schema: ClassVar[dict[str, Any]] = {}

    def __init__(self):
        self.reputation = ProviderReputation(provider_id=self.provider_id)

    @abstractmethod
    async def get_data(self, params: dict[str, Any]) -> DataResponse:
        ...

    async def validate_params(self, params: dict[str, Any]) -> bool:
        return True

    def can_handle(self, provider_id: str) -> bool:
        return provider_id == self.provider_id

    def evaluate_quality(self, response: DataResponse, threshold: float | None) -> DataQualityReport:
        passed = True
        score = 1.0
        reason = None

        if response.data is None or (isinstance(response.data, dict) and len(response.data) == 0):
            passed = False
            score = 0.0
            reason = "No data returned"
        elif response.raw_size_bytes is not None and response.raw_size_bytes < 10:
            passed = False
            score = 0.1
            reason = "Response too small — likely empty"

        if threshold is not None and score < threshold:
            passed = False

        return DataQualityReport(
            request_id=response.request_id,
            provider_id=response.provider_id,
            passed=passed,
            score=score,
            reason=reason,
        )

    @property
    def capability(self):
        from models.schemas import ProviderCapability
        return ProviderCapability(
            provider_id=self.provider_id,
            name=self.name,
            description=self.description,
            cost_hbar=self.cost_hbar,
            parameters_schema=self.parameters_schema,
            trust_score=self.reputation.trust_score,
            total_requests=self.reputation.total_requests,
            success_rate=(
                self.reputation.successful_requests / self.reputation.total_requests
                if self.reputation.total_requests > 0
                else 1.0
            ),
            avg_response_time_ms=self.reputation.response_time_ms,
            staked_hbar=self.reputation.staked_hbar,
        )
