"""A2A Auth API — JWT tokens, AP2 mandates, and authentication."""

from fastapi import APIRouter, HTTPException, Header

from core.auth import create_token, verify_token, MandateManager
from pydantic import BaseModel, Field

router = APIRouter(prefix="/auth", tags=["auth"])

_mandate_mgr: MandateManager | None = None


def get_mandate_mgr() -> MandateManager:
    global _mandate_mgr
    if _mandate_mgr is None:
        _mandate_mgr = MandateManager()
    return _mandate_mgr


class TokenRequest(BaseModel):
    agent_id: str = "hasha2a"
    ttl: int = Field(default=300, ge=60, le=3600, description="Token validity in seconds")
    scopes: list[str] = Field(default=["read"], description="Requested scopes")


class MandateRequest(BaseModel):
    agent_id: str = Field(..., description="Agent requesting spending authority")
    mandate_type: str = Field(default="intent", pattern=r"^(cart|intent|payment)$")
    max_spend_usdc: float = Field(default=10.0, ge=0.01, description="Maximum spend in USDC")
    ttl: int = Field(default=86400, ge=300, le=2592000, description="Mandate validity in seconds")


@router.post("/token")
async def request_token(body: TokenRequest):
    token = create_token(agent_id=body.agent_id, ttl=body.ttl, scopes=body.scopes)
    return {
        "token": token,
        "token_type": "Bearer",
        "expires_in": body.ttl,
        "scopes": body.scopes,
    }


@router.post("/verify")
async def verify_auth_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bearer token required")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"verified": True, "agent": payload.get("sub"), "scopes": payload.get("scopes", [])}


# AP2 Mandates ────────────────────────────────────────────────


@router.post("/mandates", status_code=201)
async def create_mandate(body: MandateRequest):
    mgr = get_mandate_mgr()
    mandate = mgr.create_mandate(
        mandate_type=body.mandate_type,
        agent_id=body.agent_id,
        max_spend_usdc=body.max_spend_usdc,
        ttl=body.ttl,
    )
    return mgr.to_dict(mandate)


@router.get("/mandates/{mandate_id}")
async def get_mandate(mandate_id: str):
    mgr = get_mandate_mgr()
    mandate = mgr.get_mandate(mandate_id)
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    return mgr.to_dict(mandate)


@router.post("/mandates/{mandate_id}/authorize")
async def authorize_mandate(mandate_id: str, body: dict):
    amount = body.get("amount_usdc")
    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="amount_usdc required")
    mgr = get_mandate_mgr()
    ok = mgr.authorize(mandate_id, amount)
    if not ok:
        mandate = mgr.get_mandate(mandate_id)
        if not mandate:
            raise HTTPException(status_code=404, detail="Mandate not found")
        raise HTTPException(status_code=402, detail="Mandate exhausted or expired")
    mandate = mgr.get_mandate(mandate_id)
    return {"authorized": True, "remaining": mgr.to_dict(mandate)["remaining"]}


@router.get("/mandates")
async def list_mandates():
    mgr = get_mandate_mgr()
    mandates = list(mgr._mandates.values())
    return {"mandates": [mgr.to_dict(m) for m in mandates], "count": len(mandates)}
