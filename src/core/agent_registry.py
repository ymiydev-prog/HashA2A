import asyncio
import time
from datetime import datetime, timezone
from hiero_sdk_python import TopicId

from core.config import Settings
from core.hedera_manager import HederaManager
from core.provider_registry import ProviderRegistry
from core.agent_directory import agent_directory, KnownAgent
from core.agent_listener import AgentListener, agent_listener
from core.agent_messaging import AgentMessaging, agent_messaging
from core.protocols.handshake import handshake_manager
from core.websocket_manager import ws_manager
from models.schemas import AgentProfile, ProviderCapability, AgentHealthCheck


class AgentRegistry:
    """
    Handles self-promotion of the HashA2A agent in the Hedera ecosystem:
    - HOL Registry registration (HCS-10 discovery)
    - Periodic promotional broadcasts to outbound HCS topic
    - Agent profile generation with live provider data
    - Health check and uptime tracking
    - Agent discovery for cross-agent communication
    - Agent-to-agent messaging and handshake
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
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._start_time = time.monotonic()
        self._last_request_at: str | None = None
        self._response_times: list[float] = []
        self._hedera_connected = False
        self._mirror_node_reachable = False

    def increment_request_count(self):
        self._total_requests_served += 1
        self._last_request_at = datetime.now(timezone.utc).isoformat()

    def record_response_time(self, ms: float):
        self._response_times.append(ms)
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]

    @property
    def avg_response_time(self) -> float | None:
        if not self._response_times:
            return None
        return sum(self._response_times) / len(self._response_times)

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._start_time

    async def check_connectivity(self):
        try:
            await self.hedera.get_or_create_inbound_topic()
            self._hedera_connected = True
        except Exception:
            self._hedera_connected = False

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.settings.mirror_node_url}/api/v1/transactions?limit=1")
                self._mirror_node_reachable = resp.status_code == 200
        except Exception:
            self._mirror_node_reachable = False

    def get_health_check(self) -> AgentHealthCheck:
        return AgentHealthCheck(
            status="healthy" if self._hedera_connected else "degraded",
            uptime_seconds=self.uptime_seconds,
            started_at=self._started_at,
            version=self.settings.agent_version,
            providers_count=len(self.providers.list_all()),
            total_requests_served=self._total_requests_served,
            avg_response_time_ms=round(self.avg_response_time, 2) if self.avg_response_time else None,
            last_request_at=self._last_request_at,
            hedera_connected=self._hedera_connected,
            mirror_node_reachable=self._mirror_node_reachable,
            agents_discovered=agent_directory.count,
            online_agents=len(agent_directory.list_online()),
        )

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
                    "providers": {p.provider_id: p.cost_hbar for p in self.providers.list_all()},
                },
                "registered_at": datetime.now(timezone.utc).isoformat(),
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
            self._last_broadcast = datetime.now(timezone.utc).isoformat()
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

        uptime_pct = min((self.uptime_seconds / 3600) * 100, 100.0) if self.uptime_seconds < 86400 else 100.0

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
            started_at=self._started_at,
            avg_response_time_ms=round(self.avg_response_time, 2) if self.avg_response_time else None,
            active_connections=len([
                c for c in handshake_manager.list_connections().values()
                if c == "connected"
            ]),
            uptime_pct=uptime_pct,
        )

    def get_discovered_agents(self, tag: str | None = None, chain: str | None = None, min_trust: float | None = None) -> list[KnownAgent]:
        """
        Retorna agentes descubiertos en el ecosistema.
        Incluye self + agentes del AgentDirectory.
        """
        agents = agent_directory.list_all()

        if tag:
            agents = [a for a in agents if tag.lower() in [t.lower() for t in a.tags]]
        if chain:
            agents = [a for a in agents if chain.lower() in [c.lower() for c in a.supported_chains]]
        if min_trust is not None:
            agents = [a for a in agents if a.trust_score >= min_trust]

        return agents

    async def initiate_handshake(self, target_agent_id: str) -> dict:
        """Inicia un handshake con otro agente."""
        target = agent_directory.get(target_agent_id)
        if not target:
            return {"error": "Agent not found", "agent_id": target_agent_id}

        inbound = await self.hedera.get_or_create_inbound_topic()
        outbound = await self.hedera.get_or_create_outbound_topic()

        msg = handshake_manager.initiate_connection(
            from_agent_id=self.settings.treasury_account,
            from_agent_name=self.settings.agent_name,
            to_agent_id=target_agent_id,
            capabilities=[p.provider_id for p in self.providers.list_all()],
        )

        try:
            await self.hedera.submit_message_to_topic(
                TopicId.from_string(target.inbound_topic),
                msg.to_json(),
            )
            return {"status": "initiated", "message": msg.model_dump()}
        except Exception as e:
            return {"error": str(e)}

    async def send_message_to_agent(
        self,
        target_agent_id: str,
        action: str,
        payload: dict | None = None,
    ) -> dict:
        """Envía un mensaje directo a otro agente."""
        target = agent_directory.get(target_agent_id)
        if not target:
            return {"error": "Agent not found"}
        if not target.inbound_topic:
            return {"error": "Agent has no inbound topic"}

        if agent_messaging is None:
            return {"error": "Messaging not initialized"}

        msg = await agent_messaging.send_message(
            to_agent_id=target_agent_id,
            to_inbound_topic=target.inbound_topic,
            action=action,
            payload=payload,
            mirror_node_url=self.settings.mirror_node_url,
        )

        if msg:
            return {"status": "sent", "message": msg.model_dump()}
        return {"error": "Failed to send message"}

    async def run_periodic_broadcast(self):
        await self.check_connectivity()

        global agent_listener, agent_messaging
        if self._hol_registered:
            agent_listener = AgentListener(
                mirror_node_url=self.settings.mirror_node_url,
                hol_registry_topic=self.settings.hol_registry_topic,
                agent_id=self.settings.treasury_account,
            )
            await agent_listener.start()

        agent_messaging = AgentMessaging(
            agent_id=self.settings.treasury_account,
            agent_name=self.settings.agent_name,
        )

        agent_messaging.register_handler("ping", self._handle_ping)
        agent_messaging.register_handler("connect", self._handle_connect)
        agent_messaging.register_handler("data_request", self._handle_data_request)

        while True:
            try:
                await self.broadcast_presence()
                await self.check_connectivity()
                agent_directory.check_stale_agents()

                stats = agent_directory.get_stats()
                await ws_manager.broadcast({
                    "type": "agent_directory_update",
                    "data": stats,
                })
            except Exception:
                pass
            await asyncio.sleep(self.settings.agent_promotional_interval)
