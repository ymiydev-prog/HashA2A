from abc import ABC, abstractmethod
from typing import ClassVar, Any
from models.schemas import DataResponse, ProviderReputation


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
        )
