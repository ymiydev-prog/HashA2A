import asyncio
import base64
import json
import time
import threading
from typing import Callable, Awaitable

import httpx
from hedera import TopicMessageQuery

from core.config import Settings
from core.hedera_manager import HederaManager
from models.schemas import PaymentRequest, RequestStatus


class PaymentEngine:
    """
    Escucha pagos de agentes usando dos mecanismos:
    1. [Primario] HCS TopicMessageQuery — recibe mensajes del Inbound Topic en tiempo real
       (HIP-991 garantiza que el fee ya fue cobrado al recibir el mensaje)
    2. [Fallo] Mirror Node REST API — polling por si la suscripción falla
    """

    def __init__(self, settings: Settings, hedera_manager: HederaManager):
        self.settings = settings
        self.hedera = hedera_manager
        self.mirror_node_url = settings.mirror_node_url.rstrip("/")
        self._pending: dict[str, PaymentRequest] = {}
        self._on_payment_callback: Callable[[str], Awaitable[None]] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._subscriber_active = False

    def on_payment_confirmed(self, callback: Callable[[str], Awaitable[None]]):
        self._on_payment_callback = callback

    def register_request(self, request: PaymentRequest):
        request.status = RequestStatus.AWAITING_PAYMENT
        self._pending[request.request_id] = request

    def deregister_request(self, request_id: str):
        self._pending.pop(request_id, None)

    def get_pending(self, request_id: str) -> PaymentRequest | None:
        return self._pending.get(request_id)

    def expire_stale_requests(self):
        now = int(time.time())
        expired = [rid for rid, req in self._pending.items() if req.expires_at < now]
        for rid in expired:
            self._pending[rid].status = RequestStatus.EXPIRED
            self._pending.pop(rid)

    async def start(self):
        self._loop = asyncio.get_running_loop()
        topic_id = await self.hedera.get_or_create_inbound_topic()

        await asyncio.sleep(5)

        thread = threading.Thread(
            target=self._run_subscription,
            args=(topic_id,),
            daemon=True,
        )
        thread.start()

        asyncio.create_task(self._run_polling_fallback())

        print(f"[PaymentEngine] 📡 HCS subscription active on {topic_id}")
        print(f"[PaymentEngine] 🔄 Mirror Node polling fallback active")

    def _run_subscription(self, topic_id):
        query = TopicMessageQuery().set_topic_id(topic_id)
        try:
            query.subscribe(
                self.hedera.client,
                self._on_subscription_error,
                self._on_message,
            )
        except TypeError:
            pass

    def _on_subscription_error(self, error, _message=None):
        pass

    def _on_message(self, message):
        self._subscriber_active = True
        try:
            payload_str = message.contents.decode("utf-8")
            payload = json.loads(payload_str)
        except Exception:
            return

        request_id = payload.get("request_id", "")
        if not request_id:
            return

        if self._loop and self._on_payment_callback:
            asyncio.run_coroutine_threadsafe(
                self._confirm_and_activate(request_id, payload),
                self._loop,
            )

    async def _confirm_and_activate(self, request_id: str, payload: dict):
        pending = self._pending.get(request_id)
        if pending is None:
            return

        pending.status = RequestStatus.PAYMENT_CONFIRMED
        print(f"[HIP-991] ✅ Fee collected for {request_id} — activating provider")

        if self._on_payment_callback:
            await self._on_payment_callback(request_id)

    async def _run_polling_fallback(self):
        while True:
            try:
                await asyncio.sleep(self.settings.payment_ttl_seconds)
                if not self._subscriber_active:
                    await self._poll_mirror_node()
            except Exception:
                pass

    async def _poll_mirror_node(self):
        self.expire_stale_requests()
        if not self._pending:
            return

        account = self.settings.treasury_account
        url = (
            f"{self.mirror_node_url}/api/v1/transactions"
            f"?account.id={account}"
            f"&transactiontype=CRYPTOTRANSFER"
            f"&order=desc&limit=50"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return
            transactions = resp.json().get("transactions", [])

        for tx in transactions:
            memo_b64 = tx.get("memo_base64", "")
            if not memo_b64:
                continue
            try:
                memo = base64.b64decode(memo_b64).decode("utf-8")
            except Exception:
                continue

            parsed = self.hedera.parse_payment_memo(memo)
            if parsed is None:
                continue

            rid = parsed["request_id"]
            pending = self._pending.get(rid)
            if pending is None or pending.status != RequestStatus.AWAITING_PAYMENT:
                continue

            transfers = tx.get("transfers", [])
            for transfer in transfers:
                if transfer.get("account") == self.settings.treasury_account:
                    amount_hbar = abs(transfer.get("amount", 0)) / 100_000_000
                    if abs(amount_hbar - pending.amount_hbar) < 0.001:
                        pending.status = RequestStatus.PAYMENT_CONFIRMED
                        print(f"[Mirror Node] ✅ Payment confirmed for {rid}")
                        if self._on_payment_callback:
                            await self._on_payment_callback(rid)
                        break
