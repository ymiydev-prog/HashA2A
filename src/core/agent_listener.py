import asyncio
import json
from datetime import datetime, timezone

import httpx

from core.agent_directory import agent_directory, KnownAgent
from core.websocket_manager import ws_manager


class AgentListener:
    """
    Escucha el HOL Registry topic y los outbound topics de agentes
    para descubrir nuevos agentes en el ecosistema Hedera.
    Usa Mirror Node REST API como fuente de verdad.
    """

    def __init__(self, mirror_node_url: str, hol_registry_topic: str, agent_id: str):
        self.mirror_node_url = mirror_node_url.rstrip("/")
        self.hol_topic = hol_registry_topic
        self.agent_id = agent_id
        self._running = False
        self._last_sequence = 0

    async def start(self):
        self._running = True
        asyncio.create_task(self._poll_hol_registry())
        asyncio.create_task(self._poll_agent_broadcasts())

    async def stop(self):
        self._running = False

    async def _poll_hol_registry(self):
        """
        Poll el HOL Registry topic para descubrir agentes registrados.
        Formato esperado: {"type": "hcs10-registration", "agent_name": "...", ...}
        """
        while self._running:
            try:
                url = (
                    f"{self.mirror_node_url}/api/v1/topics/{self.hol_topic}/messages"
                    f"?limit=25&order=desc"
                )
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        messages = data.get("messages", [])
                        for msg in messages:
                            await self._process_hol_message(msg)
            except Exception:
                pass

            await asyncio.sleep(60)

    async def _poll_agent_broadcasts(self):
        """
        Poll los outbound topics de agentes conocidos para detectar
        heartbeats y actualizaciones de presencia.
        """
        while self._running:
            try:
                online_agents = agent_directory.list_online()
                for agent in online_agents:
                    if not agent.outbound_topic or agent.agent_id == self.agent_id:
                        continue
                    await self._poll_agent_topic(agent.outbound_topic, agent.agent_id)
            except Exception:
                pass

            await asyncio.sleep(120)

    async def _poll_agent_topic(self, topic_id: str, agent_id: str):
        """Poll un outbound topic de un agente específico."""
        try:
            url = (
                f"{self.mirror_node_url}/api/v1/topics/{topic_id}/messages"
                f"?limit=5&order=desc"
            )
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    messages = data.get("messages", [])
                    for msg in messages:
                        try:
                            content = msg.get("message", "")
                            if not content:
                                b64 = msg.get("message_base64", "")
                                if b64:
                                    import base64
                                    content = base64.b64decode(b64).decode("utf-8", errors="ignore")

                            payload = json.loads(content)
                            if payload.get("type") == "agent_broadcast":
                                agent_data = payload.get("agent", {})
                                if agent_data:
                                    agent_directory.add_or_update({
                                        "agent_id": agent_id,
                                        "agent_name": agent_data.get("agent_name", ""),
                                        "description": agent_data.get("description", ""),
                                        "tags": agent_data.get("tags", []),
                                        "inbound_topic": agent_data.get("inbound_topic"),
                                        "outbound_topic": agent_data.get("outbound_topic"),
                                        "treasury_account": agent_data.get("treasury_account", agent_id),
                                        "supported_chains": ["hedera"],
                                        "total_requests": agent_data.get("total_requests_served", 0),
                                    })
                                    await ws_manager.broadcast({
                                        "type": "agent_heartbeat",
                                        "data": {
                                            "agent_id": agent_id,
                                            "agent_name": agent_data.get("agent_name", ""),
                                            "presence": "online",
                                        },
                                    })
                        except (json.JSONDecodeError, KeyError):
                            pass
        except Exception:
            pass

    async def _process_hol_message(self, msg: dict):
        """Procesa un mensaje del HOL Registry topic."""
        try:
            content = msg.get("message", "")
            if not content:
                b64 = msg.get("message_base64", "")
                if b64:
                    import base64
                    content = base64.b64decode(b64).decode("utf-8", errors="ignore")

            payload = json.loads(content)
            msg_type = payload.get("type", "")

            if msg_type == "hcs10-registration":
                agent_data = {
                    "agent_id": payload.get("treasury_account", ""),
                    "agent_name": payload.get("agent_name", "Unknown"),
                    "description": payload.get("description", ""),
                    "tags": payload.get("tags", []),
                    "inbound_topic": payload.get("inbound_topic"),
                    "outbound_topic": payload.get("outbound_topic"),
                    "treasury_account": payload.get("treasury_account", ""),
                    "supported_chains": payload.get("supported_chains", []),
                    "fees": payload.get("fees", {}),
                    "registered_at": payload.get("registered_at"),
                }

                if agent_data["agent_id"] and agent_data["agent_id"] != self.agent_id:
                    agent = agent_directory.add_or_update(agent_data)
                    await ws_manager.broadcast({
                        "type": "agent_discovered",
                        "data": {
                            "agent_id": agent.agent_id,
                            "agent_name": agent.agent_name,
                            "description": agent.description,
                            "tags": agent.tags,
                            "presence": "online",
                        },
                    })

        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    async def discover_from_api(self) -> list[KnownAgent]:
        """
        Intenta descubrir agentes desde APIs públicas de agentes conocidos.
        Útil para bootstrap inicial.
        """
        discovered = []
        known_endpoints = [
            "http://localhost:8081",
            "http://localhost:8082",
            "http://localhost:8083",
        ]

        for endpoint in known_endpoints:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{endpoint}/api/v1/agent/profile")
                    if resp.status_code == 200:
                        profile = resp.json()
                        agent = agent_directory.add_or_update({
                            "agent_id": profile.get("treasury_account", ""),
                            "agent_name": profile.get("agent_name", ""),
                            "description": profile.get("description", ""),
                            "tags": profile.get("tags", []),
                            "inbound_topic": profile.get("inbound_topic"),
                            "outbound_topic": profile.get("outbound_topic"),
                            "treasury_account": profile.get("treasury_account", ""),
                            "supported_chains": ["hedera"],
                            "total_requests": profile.get("total_requests_served", 0),
                        })
                        discovered.append(agent)
            except Exception:
                pass

        return discovered


agent_listener: AgentListener | None = None
