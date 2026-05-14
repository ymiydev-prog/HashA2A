import asyncio
from datetime import datetime
from hedera import TopicId

from core.config import Settings
from core.hedera_manager import HederaManager
from core.provider_registry import ProviderRegistry
from models.schemas import AgentProfile, ProviderCapability


class AgentRegistry:
    """
    Handles self-promotion of the HashA2A agent in the Hedera ecosystem:
    - HOL Registry registration (HCS-10 discovery)
    - Periodic promotional broadcasts to outbound HCS topic
    - Agent profile generation with live provider data
    """

    def __init__(
        self,
        settings: Settings,
        hedera_manager: HederaManager,
        provider_registry: ProviderRegistry,
    ):
        self.settings = settings
        self.hedera = hedera_manager
        self.providers = provider_registry
        self._hol_registered = False
        self._last_broadcast: str | None = None
        self._total_requests_served = 0

    def increment_request_count(self):
        self._total_requests_served += 1

    async def register_in_hol(self) -> str | None:
        """
        Register HashA2A in the Hashgraph Online (HOL) global registry
        using the HCS-10 standard format.
        """
        try:
            inbound = await self.hedera.get_or_create_inbound_topic()
            outbound = await self.hedera.get_or_create_outbound_topic()

            registration = {
                "type": "hcs10-registration",
                "protocol": "HCS-10",
                "version": "1.0",
                "agent_name": self.settings.agent_name,
                "description": self.settings.agent_description,
                "tags": self.settings.agent_tags,
                "inbound_topic": str(inbound),
                "outbound_topic": str(outbound),
                "treasury_account": self.settings.treasury_account,
                "supported_chains": ["hedera"],
                "fees": {
                    "token": "HBAR",
                    "model": "per_request",
                    "minimum": 0.01,
                },
                "registered_at": datetime.utcnow().isoformat(),
            }

            topic_id = TopicId.from_string(self.settings.hol_registry_topic)
            tx_id = await self.hedera.submit_message_to_topic(
                topic_id,
                registration,
            )
            self._hol_registered = True
            return tx_id
        except Exception:
            return None

    async def broadcast_presence(self) -> str | None:
        profile = await self.get_profile()
        try:
            tx_id = await self.hedera.publish_agent_broadcast(
                profile.model_dump(mode="json")
            )
            self._last_broadcast = datetime.utcnow().isoformat()
            return tx_id
        except Exception:
            return None

    async def get_profile(self) -> AgentProfile:
        providers = self.providers.list_capabilities()
        inbound = None
        outbound = None
        try:
            inbound = str(await self.hedera.get_or_create_inbound_topic())
            outbound = str(await self.hedera.get_or_create_outbound_topic())
        except Exception:
            pass

        return AgentProfile(
            agent_name=self.settings.agent_name,
            agent_version=self.settings.agent_version,
            description=self.settings.agent_description,
            tags=self.settings.agent_tags,
            hol_registry_topic=self.settings.hol_registry_topic,
            inbound_topic=inbound,
            outbound_topic=outbound,
            treasury_account=self.settings.treasury_account,
            supported_providers=providers,
            total_requests_served=self._total_requests_served,
            last_broadcast=self._last_broadcast,
        )

    async def run_periodic_broadcast(self):
        while True:
            try:
                await self.broadcast_presence()
            except Exception:
                pass
            await asyncio.sleep(self.settings.agent_promotional_interval)
