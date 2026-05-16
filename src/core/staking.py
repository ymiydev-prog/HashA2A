import time
from pydantic import BaseModel, Field

from core.base_provider import BaseDataProvider


class SlashingEvent(BaseModel):
    provider_id: str
    reason: str
    slashed_amount: float
    timestamp: str
    severity: str = "low"


class StakingManager:
    """
    Gestiona staking y slashing de proveedores.
    Implementa penalizaciones automáticas por mal comportamiento.
    """

    MIN_STAKE = 10.0
    MAX_SLASH_PCT = 0.5

    def __init__(self):
        self._slash_history: list[SlashingEvent] = []

    def slash_provider(
        self,
        provider: BaseDataProvider,
        reason: str,
        severity: str = "low",
    ) -> SlashingEvent:
        current_stake = provider.reputation.staked_hbar

        if current_stake < self.MIN_STAKE:
            return SlashingEvent(
                provider_id=provider.provider_id,
                reason=reason,
                slashed_amount=0.0,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                severity=severity,
            )

        slash_pct = {"low": 0.05, "medium": 0.15, "high": 0.3, "critical": 0.5}.get(severity, 0.05)
        slashed_amount = min(current_stake * slash_pct, current_stake * self.MAX_SLASH_PCT)

        provider.reputation.staked_hbar -= slashed_amount
        provider.reputation.accuracy_score = max(0, provider.reputation.accuracy_score - (slash_pct * 100))

        event = SlashingEvent(
            provider_id=provider.provider_id,
            reason=reason,
            slashed_amount=round(slashed_amount, 4),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            severity=severity,
        )
        self._slash_history.append(event)

        return event

    def get_slash_history(self, provider_id: str | None = None) -> list[SlashingEvent]:
        if provider_id:
            return [e for e in self._slash_history if e.provider_id == provider_id]
        return self._slash_history

    def get_provider_risk_level(self, provider: BaseDataProvider) -> str:
        recent_slashes = [
            e for e in self._slash_history
            if e.provider_id == provider.provider_id
        ]
        total_slashed = sum(e.slashed_amount for e in recent_slashes)
        current_stake = provider.reputation.staked_hbar

        if current_stake == 0:
            return "critical"
        if total_slashed > current_stake * 0.3:
            return "high"
        if total_slashed > current_stake * 0.1:
            return "medium"
        return "low"
