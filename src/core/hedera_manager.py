import uuid
import json
import hashlib
from datetime import datetime

from hiero_sdk_python import (
    AccountId,
    Client,
    PrivateKey,
    TopicId,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
    TopicMessageQuery,
    CustomFixedFee,
    Hbar,
)
from core.config import Settings


class HederaManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Client | None = None
        self._operator_key: PrivateKey | None = None
        self.audit_topic_id: TopicId | None = None
        self.inbound_topic_id: TopicId | None = None
        self.outbound_topic_id: TopicId | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._initialize()
        return self._client

    @property
    def operator_key(self) -> PrivateKey:
        if self._operator_key is None:
            self._initialize()
        return self._operator_key

    def _initialize(self):
        network = self.settings.hedera_network
        if network == "testnet":
            self._client = Client.for_testnet()
        elif network == "mainnet":
            self._client = Client.for_mainnet()
        else:
            self._client = Client.for_previewnet()

        op_id = AccountId.from_string(self.settings.hedera_operator_id)
        op_key = PrivateKey.from_string(self.settings.hedera_operator_key)
        self._client.set_operator(op_id, op_key)
        self._operator_key = op_key

    def close(self):
        try:
            if self._client:
                self._client.close()
        except Exception:
            pass

    def generate_request_id(self) -> str:
        return str(uuid.uuid4())

    def generate_payment_memo(self, request_id: str, provider_id: str) -> str:
        return f"HASHA2A:{request_id}:{provider_id}"

    def parse_payment_memo(self, memo: str) -> dict | None:
        parts = memo.split(":")
        if len(parts) == 3 and parts[0] == "HASHA2A":
            return {"request_id": parts[1], "provider_id": parts[2]}
        return None

    async def create_topic(self, memo: str) -> TopicId:
        tx = (
            TopicCreateTransaction()
            .set_topic_memo(memo)
            .set_admin_key(self.operator_key.public_key())
            .freeze_with(self.client)
            .sign(self.operator_key)
        )
        response = await tx.execute_async(self.client)
        receipt = await response.get_receipt_async(self.client)
        return receipt.topic_id

    async def create_topic_with_fees(self, memo: str, fee_hbar: float) -> TopicId:
        collector = AccountId.from_string(
            self.settings.hip991_fee_collector or self.settings.treasury_account
        )
        amount_tinybar = int(fee_hbar * 100_000_000)
        operator_pub = self.operator_key.public_key()

        tx = (
            TopicCreateTransaction()
            .set_topic_memo(memo)
            .set_admin_key(operator_pub)
            .set_fee_schedule_key(operator_pub)
            .set_fee_exempt_keys([operator_pub])
            .set_custom_fees([
                CustomFixedFee()
                    .set_amount_in_tinybars(amount_tinybar)
                    .set_fee_collector_account_id(collector)
            ])
            .freeze_with(self.client)
            .sign(self.operator_key)
        )
        response = await tx.execute_async(self.client)
        receipt = await response.get_receipt_async(self.client)
        return receipt.topic_id

    async def get_or_create_audit_topic(self) -> TopicId:
        if self.audit_topic_id is not None:
            return self.audit_topic_id
        self.audit_topic_id = await self.create_topic(
            f"HashA2A Audit Trail v{self.settings.agent_version}"
        )
        return self.audit_topic_id

    async def get_or_create_inbound_topic(self) -> TopicId:
        if self.inbound_topic_id is not None:
            return self.inbound_topic_id
        self.inbound_topic_id = await self.create_topic_with_fees(
            f"HashA2A Inbound - {self.settings.agent_name}",
            self.settings.hip991_fee_hbar,
        )
        return self.inbound_topic_id

    async def get_or_create_outbound_topic(self) -> TopicId:
        if self.outbound_topic_id is not None:
            return self.outbound_topic_id
        self.outbound_topic_id = await self.create_topic(
            f"HashA2A Outbound - {self.settings.agent_name}"
        )
        return self.outbound_topic_id

    async def submit_message_to_topic(
        self, topic_id: TopicId, message: dict | str
    ) -> str:
        if isinstance(message, dict):
            message = json.dumps(message)

        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message(message)
            .freeze_with(self.client)
            .sign(self.operator_key)
        )
        response = await tx.execute_async(self.client)
        receipt = await response.get_receipt_async(self.client)
        return str(receipt.transaction_id)

    def compute_data_hash(self, data: dict) -> str:
        raw = json.dumps(data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def publish_consensus_record(
        self,
        request_id: str,
        provider_id: str,
        query: dict,
        response: dict,
        analysis: str | None,
        provider_trust_score: float,
        payment_amount: float,
    ) -> str:
        from models.schemas import ConsensusRecord

        record = ConsensusRecord(
            request_id=request_id,
            provider_id=provider_id,
            query_hash=self.compute_data_hash(query),
            response_hash=self.compute_data_hash(response),
            analysis_hash=self.compute_data_hash({"text": analysis}) if analysis else None,
            payment_amount=payment_amount,
            provider_trust_score=provider_trust_score,
            timestamp=datetime.utcnow().isoformat(),
        )

        topic_id = await self.get_or_create_audit_topic()
        tx_id = await self.submit_message_to_topic(
            topic_id, record.model_dump(mode="json")
        )
        return tx_id

    async def publish_agent_broadcast(self, profile: dict) -> str:
        topic_id = await self.get_or_create_outbound_topic()
        payload = {
            "type": "agent_broadcast",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": profile,
        }
        return await self.submit_message_to_topic(topic_id, payload)
