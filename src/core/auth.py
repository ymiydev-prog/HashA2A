"""A2A Auth — ephemeral JWT tokens, mandate support, and authentication."""

import time
import uuid
from typing import Any

try:
    import jwt as pyjwt
    HAS_JWT = True
except ImportError:
    pyjwt = None
    HAS_JWT = False


SECRET_KEY = None  # set on first use


def _get_secret() -> str:
    global SECRET_KEY
    if SECRET_KEY is None:
        SECRET_KEY = uuid.uuid4().hex + uuid.uuid4().hex
    return SECRET_KEY


def create_token(agent_id: str = "hasha2a", ttl: int = 300, scopes: list[str] | None = None) -> str:
    if not HAS_JWT:
        return f"mock_token_{agent_id}_{int(time.time())}"
    payload = {
        "sub": agent_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
        "jti": uuid.uuid4().hex[:16],
        "scopes": scopes or ["read"],
    }
    return pyjwt.encode(payload, _get_secret(), algorithm="HS256")


def verify_token(token: str) -> dict[str, Any] | None:
    if not HAS_JWT:
        if token.startswith("mock_token_"):
            parts = token.split("_")
            if len(parts) >= 3:
                return {"sub": parts[2], "scopes": ["read"]}
        return None
    try:
        return pyjwt.decode(token, _get_secret(), algorithms=["HS256"])
    except Exception:
        return None


class Mandate:
    """AP2-style cryptographic mandate for agent spending authorization."""

    def __init__(self, mandate_id: str, mandate_type: str, agent_id: str,
                 max_spend_usdc: float, expires_at: int, signature: str | None = None):
        self.mandate_id = mandate_id
        self.mandate_type = mandate_type  # "cart", "intent", "payment"
        self.agent_id = agent_id
        self.max_spend_usdc = max_spend_usdc
        self.expires_at = expires_at
        self.signature = signature
        self.spent_so_far = 0.0

    def is_valid(self) -> bool:
        return time.time() < self.expires_at and self.spent_so_far < self.max_spend_usdc

    def authorize(self, amount_usdc: float) -> bool:
        if not self.is_valid():
            return False
        if self.spent_so_far + amount_usdc > self.max_spend_usdc:
            return False
        self.spent_so_far += amount_usdc
        return True


class MandateManager:
    """Manages AP2 mandates for agent spending limits."""

    def __init__(self):
        self._mandates: dict[str, Mandate] = {}

    def create_mandate(self, mandate_type: str, agent_id: str,
                       max_spend_usdc: float, ttl: int = 86400) -> Mandate:
        mandate = Mandate(
            mandate_id=str(uuid.uuid4()),
            mandate_type=mandate_type,
            agent_id=agent_id,
            max_spend_usdc=max_spend_usdc,
            expires_at=int(time.time()) + ttl,
        )
        self._mandates[mandate.mandate_id] = mandate
        return mandate

    def get_mandate(self, mandate_id: str) -> Mandate | None:
        return self._mandates.get(mandate_id)

    def authorize(self, mandate_id: str, amount_usdc: float) -> bool:
        mandate = self._mandates.get(mandate_id)
        if not mandate:
            return False
        return mandate.authorize(amount_usdc)

    def to_dict(self, mandate: Mandate) -> dict:
        return {
            "mandate_id": mandate.mandate_id,
            "mandate_type": mandate.mandate_type,
            "agent_id": mandate.agent_id,
            "max_spend_usdc": mandate.max_spend_usdc,
            "spent_so_far": round(mandate.spent_so_far, 2),
            "remaining": round(mandate.max_spend_usdc - mandate.spent_so_far, 2),
            "expires_at": mandate.expires_at,
            "is_valid": mandate.is_valid(),
        }
