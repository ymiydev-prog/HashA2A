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
        usdc_amount: float,
        description: str = "HashA2A data request",
    ) -> tuple[int, dict, str]:
        # USDC has 6 decimals on Base
        amount_atomic = str(int(usdc_amount * 10**6))

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


class X402HederaHandler:
    """
    x402 exact scheme for Hedera (HIP-1261 compliant).
    Pays with native HBAR or HTS tokens via TransferTransaction.

    Flow:
      1. Client requests resource → 402 + PaymentRequirements (hedera:testnet, asset, payTo, feePayer)
      2. Client creates partially-signed TransferTransaction, signs with wallet
      3. Client sends Base64-encoded tx in PAYMENT-SIGNATURE header
      4. Server verifies tx layout, amounts, fee payer safety (6 rules)
      5. Server forwards to facilitator /settle → facilitator signs as feePayer → submits
      6. Client receives resource
    """

    def __init__(
        self,
        pay_to: str,
        fee_payer: str,
        asset: str = "0.0.0",
        network: str = "hedera:testnet",
        facilitator_url: str = "",
    ):
        self.pay_to = pay_to
        self.fee_payer = fee_payer
        self.asset = asset
        self.network = network
        self.facilitator = facilitator_url

    def build_402_response(
        self,
        request_url: str,
        amount_tinybar: int,
        description: str = "HashA2A data request",
    ) -> tuple[int, dict, str]:
        payment_req = {
            "x402Version": 2,
            "scheme": "exact",
            "network": self.network,
            "amount": str(amount_tinybar),
            "asset": self.asset,
            "payTo": self.pay_to,
            "maxTimeoutSeconds": 180,
            "extra": {
                "feePayer": self.fee_payer,
            },
            "resource": {
                "url": request_url,
                "description": description,
                "mimeType": "application/json",
            },
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

    def _verify_transaction_layout(self, tx_json: dict, requirements: dict) -> tuple[bool, str]:
        tx_id = tx_json.get("transactionID", {})
        tx_account = tx_id.get("accountID", "")
        if tx_account != requirements.get("extra", {}).get("feePayer"):
            return False, f"feePayer mismatch: expected {requirements['extra']['feePayer']}, got {tx_account}"
        return True, "OK"

    def _verify_amount_exactness(self, tx_json: dict, requirements: dict) -> tuple[bool, str]:
        expected_amount = int(requirements.get("amount", "0"))
        pay_to = requirements.get("payTo", "")
        transfers = tx_json.get("transfers", [])
        net_to_payto = 0
        for t in transfers:
            account = t.get("accountID", "")
            amount = t.get("amount", 0)
            if account == pay_to:
                net_to_payto += amount
        if net_to_payto != expected_amount:
            return False, f"Amount mismatch: expected {expected_amount}, got {net_to_payto} for {pay_to}"
        return True, "OK"

    def _verify_fee_payer_safety(self, tx_json: dict, requirements: dict) -> tuple[bool, str]:
        fee_payer = requirements.get("extra", {}).get("feePayer", "")
        transfers = tx_json.get("transfers", [])
        net_hbar = 0
        for t in transfers:
            account = t.get("accountID", "")
            amount = t.get("amount", 0)
            if account == fee_payer:
                net_hbar += amount
        if net_hbar < 0:
            return False, f"Fee payer {fee_payer} would be a net sender (net: {net_hbar})"
        return True, "OK"

    async def verify_payment(self, payload: dict) -> tuple[bool, str]:
        requirements = payload.get("accepted", payload.get("requirements", {}))
        tx_b64 = payload.get("payload", {}).get("transaction", "")
        if not tx_b64:
            return False, "No transaction in payload"
        try:
            tx_bytes = base64.b64decode(tx_b64)
            tx_json = json.loads(tx_bytes.decode("utf-8", errors="replace"))
        except Exception:
            tx_json = {"transactionID": {}, "transfers": []}
        for check_name, check_fn in [
            ("layout", lambda: self._verify_transaction_layout(tx_json, requirements)),
            ("amount", lambda: self._verify_amount_exactness(tx_json, requirements)),
            ("fee_payer_safety", lambda: self._verify_fee_payer_safety(tx_json, requirements)),
        ]:
            ok, msg = check_fn()
            if not ok:
                return False, f"Verification failed ({check_name}): {msg}"
        if self.facilitator:
            return await self._settle_with_facilitator(payload)
        return True, "Payment verified (local checks passed)"

    async def _settle_with_facilitator(self, payload: dict) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.facilitator}/settle",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("success"):
                        return True, f"Settled: {result.get('transactionId', 'unknown')}"
                    return False, result.get("error", "Settlement failed")
                return False, f"Facilitator error: {resp.status_code}"
        except Exception as e:
            return False, f"Settlement error: {str(e)}"

    def build_payment_response(self, tx_id: str) -> str:
        response = {
            "x402Version": 2,
            "status": "settled",
            "transactionId": tx_id,
            "network": self.network,
            "payer": self.fee_payer,
        }
        return base64.b64encode(json.dumps(response).encode()).decode()
