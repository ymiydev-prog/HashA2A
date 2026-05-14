import asyncio
import base64
import time
from typing import Callable, Awaitable

import httpx
from core.config import Settings
from core.hedera_manager import HederaManager
from models.schemas import PaymentRequest, RequestStatus


class PaymentEngine:
    def __init__(self, settings: Settings, hedera_manager: HederaManager):
        self.settings = settings
        self.hedera = hedera_manager
        self.mirror_node_url = settings.mirror_node_url.rstrip("/")
        self._pending: dict[str, PaymentRequest] = {}
        self._last_seen_timestamp: str | None = None
        self._on_payment_callback: Callable[[str], Awaitable[None]] | None = None

    def on_payment_confirmed(self, callback: Callable[[str], Awaitable[None]]):
        self._on_payment_callback = callback

    def register_request(self, request: PaymentRequest):
        self._pending[request.request_id] = request

    def deregister_request(self, request_id: str):
        self._pending.pop(request_id, None)

    def get_pending(self, request_id: str) -> PaymentRequest | None:
        return self._pending.get(request_id)

    def expire_stale_requests(self):
        now = int(time.time())
        expired = [
            rid for rid, req in self._pending.items()
            if req.expires_at < now
        ]
        for rid in expired:
            req = self._pending[rid]
            req.status = RequestStatus.EXPIRED
            self._pending.pop(rid)

    async def fetch_transactions(self) -> list[dict]:
        account = self.settings.treasury_account
        url = (
            f"{self.mirror_node_url}/api/v1/transactions"
            f"?account.id={account}"
            f"&transactiontype=CRYPTOTRANSFER"
            f"&order=desc&limit=50"
        )
        if self._last_seen_timestamp:
            url += f"&timestamp=gt:{self._last_seen_timestamp}"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json().get("transactions", [])

    def check_transaction_match(
        self, tx: dict, pending: PaymentRequest
    ) -> bool:
        memo_b64 = tx.get("memo_base64", "")
        if not memo_b64:
            return False

        try:
            memo = base64.b64decode(memo_b64).decode("utf-8")
        except Exception:
            return False

        parsed = self.hedera.parse_payment_memo(memo)
        if parsed is None or parsed["request_id"] != pending.request_id:
            return False

        transfers = tx.get("transfers", [])
        for transfer in transfers:
            if transfer.get("account") == self.settings.treasury_account:
                amount_hbar = abs(transfer.get("amount", 0)) / 100_000_000
                if abs(amount_hbar - pending.amount_hbar) < 0.001:
                    return True
        return False

    async def check_payments(self) -> list[str]:
        self.expire_stale_requests()
        if not self._pending:
            return []

        transactions = await self.fetch_transactions()

        if transactions:
            self._last_seen_timestamp = transactions[0].get("consensus_timestamp")

        confirmed: list[str] = []
        for tx in transactions:
            for rid, pending in list(self._pending.items()):
                if pending.status == RequestStatus.AWAITING_PAYMENT:
                    if self.check_transaction_match(tx, pending):
                        pending.status = RequestStatus.PAYMENT_CONFIRMED
                        confirmed.append(rid)
        return confirmed

    async def run_forever(self):
        while True:
            try:
                confirmed = await self.check_payments()
                for request_id in confirmed:
                    if self._on_payment_callback:
                        await self._on_payment_callback(request_id)
            except Exception:
                pass
            await asyncio.sleep(self.settings.payment_polling_interval)
