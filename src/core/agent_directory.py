import time
from typing import Any
from pydantic import BaseModel, Field


class AgentPresence(str):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class KnownAgent(BaseModel):
    agent_name: str
    agent_id: str
    description: str = ""
    tags: list[str] = []
    inbound_topic: str | None = None
    outbound_topic: str | None = None
    treasury_account: str = ""
    supported_chains: list[str] = []
    fees: dict[str, Any] = {}
    trust_score: float = 50.0
    total_requests: int = 0
    first_seen: str = ""
    last_seen: str = ""
    registered_at: str | None = None
    presence: str = "unknown"
    heartbeat_count: int = 0
    response_count: int = 0
    reputation_score: float = 50.0


class AgentDirectory:
    """
    Almacena y gestiona agentes descubiertos en el ecosistema Hedera.
    Escucha el HOL Registry topic y mantiene un directorio de agentes
    con tracking de presencia (online/offline).
    """

    OFFLINE_THRESHOLD = 300.0  # 5 minutos sin heartbeat = offline

    def __init__(self):
        self._agents: dict[str, KnownAgent] = {}

    def add_or_update(self, agent_data: dict[str, Any]) -> KnownAgent:
        agent_id = agent_data.get("agent_id", agent_data.get("treasury_account", ""))
        if not agent_id:
            raise ValueError("agent_id or treasury_account is required")

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        existing = self._agents.get(agent_id)

        if existing:
            existing.last_seen = now
            existing.heartbeat_count += 1
            existing.presence = "online"
            if agent_data.get("agent_name"):
                existing.agent_name = agent_data["agent_name"]
            if agent_data.get("description"):
                existing.description = agent_data["description"]
            if agent_data.get("tags"):
                existing.tags = agent_data["tags"]
            if agent_data.get("inbound_topic"):
                existing.inbound_topic = agent_data["inbound_topic"]
            if agent_data.get("outbound_topic"):
                existing.outbound_topic = agent_data["outbound_topic"]
            if agent_data.get("supported_chains"):
                existing.supported_chains = agent_data["supported_chains"]
            if agent_data.get("fees"):
                existing.fees = agent_data["fees"]
            if agent_data.get("total_requests") is not None:
                existing.total_requests = agent_data["total_requests"]
            return existing

        agent = KnownAgent(
            agent_name=agent_data.get("agent_name", "Unknown"),
            agent_id=agent_id,
            description=agent_data.get("description", ""),
            tags=agent_data.get("tags", []),
            inbound_topic=agent_data.get("inbound_topic"),
            outbound_topic=agent_data.get("outbound_topic"),
            treasury_account=agent_data.get("treasury_account", agent_id),
            supported_chains=agent_data.get("supported_chains", []),
            fees=agent_data.get("fees", {}),
            trust_score=agent_data.get("trust_score", 50.0),
            total_requests=agent_data.get("total_requests", 0),
            first_seen=now,
            last_seen=now,
            registered_at=agent_data.get("registered_at"),
            presence="online",
            heartbeat_count=1,
        )
        self._agents[agent_id] = agent
        return agent

    def get(self, agent_id: str) -> KnownAgent | None:
        return self._agents.get(agent_id)

    def list_all(self, presence_filter: str | None = None) -> list[KnownAgent]:
        agents = list(self._agents.values())
        if presence_filter:
            agents = [a for a in agents if a.presence == presence_filter]
        return agents

    def list_online(self) -> list[KnownAgent]:
        return [a for a in self._agents.values() if a.presence == "online"]

    def remove(self, agent_id: str) -> bool:
        return self._agents.pop(agent_id, None) is not None

    def update_presence(self, agent_id: str, presence: str):
        agent = self._agents.get(agent_id)
        if agent:
            agent.presence = presence
            if presence == "online":
                agent.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                agent.heartbeat_count += 1

    def check_stale_agents(self):
        now = time.monotonic()
        for agent in self._agents.values():
            try:
                last_seen_ts = time.mktime(time.strptime(agent.last_seen, "%Y-%m-%dT%H:%M:%SZ"))
                if (now - last_seen_ts) > self.OFFLINE_THRESHOLD:
                    agent.presence = "offline"
            except (ValueError, OverflowError):
                agent.presence = "unknown"

    def get_stats(self) -> dict:
        agents = self._agents.values()
        return {
            "total_agents": len(self._agents),
            "online_agents": sum(1 for a in agents if a.presence == "online"),
            "offline_agents": sum(1 for a in agents if a.presence == "offline"),
            "unknown_agents": sum(1 for a in agents if a.presence == "unknown"),
        }

    @property
    def count(self) -> int:
        return len(self._agents)


agent_directory = AgentDirectory()
