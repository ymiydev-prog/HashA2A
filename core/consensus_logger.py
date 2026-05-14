import json
import hashlib
import time
from datetime import datetime
from typing import Any

from core.hedera_manager import HederaManager
from models.schemas import ConsensusRecord, DataResponse


class ConsensusLogger:
    def __init__(self, hedera_manager: HederaManager):
        self.hedera = hedera_manager

    def compute_hash(self, data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def log_response(
        self,
        response: DataResponse,
        query: dict,
        payment_amount: float,
        provider_trust_score: float,
        client_agent_id: str | None = None,
    ) -> str:
        record = ConsensusRecord(
            request_id=response.request_id,
            provider_id=response.provider_id,
            client_agent_id=client_agent_id,
            query_hash=self.compute_hash(query),
            response_hash=self.compute_hash(response.data or {}),
            analysis_hash=self.compute_hash({"text": response.analysis}) if response.analysis else None,
            payment_amount=payment_amount,
            provider_trust_score=provider_trust_score,
            timestamp=datetime.utcnow().isoformat(),
        )

        return await self.hedera.submit_message_to_topic(
            await self.hedera.get_or_create_audit_topic(),
            record.model_dump(mode="json"),
        )

    async def log_broadcast(self, message_type: str, payload: dict) -> str:
        topic_id = await self.hedera.get_or_create_outbound_topic()
        entry = {
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        return await self.hedera.submit_message_to_topic(topic_id, entry)
