import base64
import json
import time
import uuid
from typing import Any

import httpx


class X402Handler:
    """
    Implementa el protocolo x402 v2 (Coinbase).
    HTTP 402 Payment Required → el agente paga USDC → recibe datos.

    Flujo:
      1. Cliente pide recurso → 402 + PAYMENT-REQUIRED header
      2. Cliente paga USDC y retorna con PAYMENT-SIGNATURE header
      3. Servidor verifica pago (vía facilitator) → entrega recurso
    """

    FACILITATOR_URL = "https://x402.org/facilitator"
    SUPPORTED_NETWORKS = {
        "eip155:8453": "base",
        "eip155:137": "polygon",
    }

    def __init__(
        self,
        treasury_address: str,
        usdc_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        network: str = "eip155:8453",
        facilitator_url: str = FACILITATOR_URL,
    ):
        self.treasury = treasury_address
        self.usdc = usdc_address
        self.network = network
        self.facilitator = facilitator_url
        self._pending: dict[str, dict] = {}

    def build_402_response(
        self,
        request_url: str,
        amount_hbar: float,
        description: str = "HashA2A data request",
    ) -> tuple[int, dict, str]:
        amount_usdc = int(amount_hbar * 100)  # 1 HBAR ≈ 0.20 USDC approx
        amount_atomic = str(amount_usdc * 10**6)

        payment_req = {
            "x402Version": 2,
            "error": "PAYMENT-SIGNATURE header is required",
            "resource": {
                "url": request_url,
                "description": description,
                "mimeType": "application/json",
            },
            "accepts": [
                {
                    "scheme": "exact",
                    "network": self.network,
                    "amount": amount_atomic,
                    "asset": self.usdc,
                    "payTo": self.treasury,
                    "maxTimeoutSeconds": 120,
                    "extra": {"name": "USDC", "version": "2"},
                }
            ],
            "extensions": {},
        }

        encoded = base64.b64encode(json.dumps(payment_req).encode()).decode()
        return 402, {"PAYMENT-REQUIRED": encoded}, encoded

    def extract_payment_payload(self, headers: dict) -> dict | None:
        raw = headers.get("payment-signature") or headers.get("PAYMENT-SIGNATURE")
        if not raw:
            return None
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            return json.loads(decoded)
        except Exception:
            return None

    async def verify_payment(self, payload: dict) -> tuple[bool, str]:
        """
        Verifica el pago vía facilitator x402.org.
        Retorna (exitoso, mensaje).
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.facilitator}/verify",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("verified"):
                        return True, "Payment verified"
                    return False, result.get("error", "Verification failed")
                return False, f"Facilitator error: {resp.status_code}"
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    async def settle_payment(self, payload: dict) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.facilitator}/settle",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    return True, "Payment settled"
                return False, f"Settlement error: {resp.status_code}"
        except Exception as e:
            return False, f"Settlement error: {str(e)}"

    def build_payment_response(self, tx_hash: str) -> str:
        response = {
            "x402Version": 2,
            "status": "settled",
            "transaction": {"hash": tx_hash, "network": self.network},
        }
        return base64.b64encode(json.dumps(response).encode()).decode()


class X402Middleware:
    """
    Middleware que intercepta requests y aplica x402 si el recurso requiere pago.
    Se integra con el PaymentEngine existente.
    """

    def __init__(self, x402_handler: X402Handler, request_cost_map: dict[str, float]):
        self.handler = x402_handler
        self.cost_map = request_cost_map

    def is_protected(self, path: str) -> float | None:
        for prefix, cost in self.cost_map.items():
            if path.startswith(prefix):
                return cost
        return None

    async def process_request(self, path: str, headers: dict, body: dict | None = None):
        cost = self.is_protected(path)
        if cost is None:
            return None

        payload = self.handler.extract_payment_payload(headers)

        if payload is None:
            return self.handler.build_402_response(path, cost)

        verified, msg = await self.handler.verify_payment(payload)
        if not verified:
            return 402, {}, msg

        return None
