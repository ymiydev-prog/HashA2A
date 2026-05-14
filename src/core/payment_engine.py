import asyncio
import json
import time
import threading
from typing import Callable, Awaitable

from hedera import TopicMessageQuery

from core.config import Settings
from core.hedera_manager import HederaManager
from models.schemas import PaymentRequest, RequestStatus


class PaymentEngine:
    def __init__(self, settings: Settings, hedera_manager: HederaManager):
        self.settings = settings
        self.hedera = hedera_manager
        self._pending: dict[str, PaymentRequest] = {}
        self._on_payment_callback: Callable[[str], Awaitable[None]] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._subscription = None

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
        expired = [
            rid for rid, req in self._pending.items()
            if req.expires_at < now
        ]
        for rid in expired:
            self._pending[rid].status = RequestStatus.EXPIRED
            self._pending.pop(rid)

    async def start(self):
        """
        Subscribe to the inbound HCS topic.
        When an agent submits a message, HIP-991 auto-collects the fee.
        We receive the message and match it to a pending request.
        """
        self._loop = asyncio.get_running_loop()
        topic_id = await self.hedera.get_or_create_inbound_topic()

        thread = threading.Thread(
            target=self._run_subscription,
            args=(topic_id,),
            daemon=True,
        )
        thread.start()

    def _run_subscription(self, topic_id):
        """Runs in background thread — listens for incoming HCS messages."""
        query = TopicMessageQuery().set_topic_id(topic_id)

        query.subscribe(
            self.hedera.client,
            self._on_subscription_error,
            self._on_message,
        )

    def _on_subscription_error(self, error):
        print(f"[HIP-991] Subscription error: {error}")

    def _on_message(self, message):
        """Called when an agent submits to the inbound topic (fee collected by HIP-991)."""
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
        """
        HIP-991 ya cobró el fee automáticamente.
        Solo actualizamos estado y activamos el provider.
        """
        pending = self._pending.get(request_id)
        if pending is None:
            return

        pending.status = RequestStatus.PAYMENT_CONFIRMED
        print(f"[HIP-991] ✅ Fee collected for {request_id} — activating provider")

        if self._on_payment_callback:
            await self._on_payment_callback(request_id)

    def stop(self):
        self._subscription = None

    async def run_forever(self):
        """Kept for backward compatibility — not used in HIP-991 mode."""
        await asyncio.Future()
