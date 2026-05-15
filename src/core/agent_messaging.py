import time
import json
import asyncio
from typing import Any, Callable, Awaitable
from pydantic import BaseModel

import httpx

from core.protocols.handshake import HandshakeMessage, HandshakeState, handshake_manager


class AgentMessage(BaseModel):
    type: str = "message"
    action: str  # "ping", "pong", "data_request", "data_response", "quote", "status"
    from_agent_id: str
    from_agent_name: str
    to_agent_id: str
    payload: dict[str, Any] = {}
    timestamp: str = ""
    correlation_id: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.correlation_id:
            import uuid
            self.correlation_id = str(uuid.uuid4())

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "AgentMessage":
        data = json.loads(raw)
        return cls(**data)


class AgentMessaging:
    """
    Sistema de mensajería directa entre agentes vía HCS topics.
    Permite enviar y recibir mensajes a otros agentes usando su
    inbound topic como canal de comunicación.
    """

    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self._handlers: dict[str, Callable[[AgentMessage], Awaitable[AgentMessage | None]]] = {}
        self._pending_responses: dict[str, asyncio.Future] = {}
        self._message_log: list[dict] = []

    def register_handler(
        self,
        action: str,
        handler: Callable[[AgentMessage], Awaitable[AgentMessage | None]],
    ):
        self._handlers[action] = handler

    async def send_message(
        self,
        to_agent_id: str,
        to_inbound_topic: str,
        action: str,
        payload: dict[str, Any] | None = None,
        mirror_node_url: str = "https://testnet.mirrornode.hedera.com",
    ) -> AgentMessage | None:
        """
        Envía un mensaje a otro agente vía su inbound topic.
        Usa el Mirror Node REST API para submitir un mensaje HCS.
        """
        msg = AgentMessage(
            action=action,
            from_agent_id=self.agent_id,
            from_agent_name=self.agent_name,
            to_agent_id=to_agent_id,
            payload=payload or {},
        )

        self._log_message("sent", msg)

        try:
            url = f"{mirror_node_url.rstrip('/')}/api/v1/topics/{to_inbound_topic}/messages"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json={"message": msg.to_json()})
                if resp.status_code in (200, 201):
                    return msg
        except Exception:
            pass

        return None

    async def send_with_response(
        self,
        to_agent_id: str,
        to_inbound_topic: str,
        action: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 30.0,
        mirror_node_url: str = "https://testnet.mirrornode.hedera.com",
    ) -> AgentMessage | None:
        """
        Envía un mensaje y espera respuesta.
        """
        msg = AgentMessage(
            action=action,
            from_agent_id=self.agent_id,
            from_agent_name=self.agent_name,
            to_agent_id=to_agent_id,
            payload=payload or {},
        )

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending_responses[msg.correlation_id] = future

        try:
            url = f"{mirror_node_url.rstrip('/')}/api/v1/topics/{to_inbound_topic}/messages"
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(url, json={"message": msg.to_json()})

            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            return None
        finally:
            self._pending_responses.pop(msg.correlation_id, None)

    async def process_incoming_message(self, raw: str) -> AgentMessage | None:
        """
        Procesa un mensaje entrante y ejecuta el handler correspondiente.
        Retorna la respuesta si el handler genera una.
        """
        try:
            msg = AgentMessage.from_json(raw)
        except (json.JSONDecodeError, ValueError):
            return None

        self._log_message("received", msg)

        if msg.to_agent_id != self.agent_id:
            return None

        handler = self._handlers.get(msg.action)
        if handler:
            try:
                response = await handler(msg)
                if response:
                    self._log_message("response", response)

                    if msg.correlation_id in self._pending_responses:
                        self._pending_responses[msg.correlation_id].set_result(response)

                    return response
            except Exception:
                pass

        return None

    async def send_ping(
        self,
        to_agent_id: str,
        to_inbound_topic: str,
        mirror_node_url: str = "https://testnet.mirrornode.hedera.com",
    ) -> bool:
        """Envía un ping a otro agente para verificar conectividad."""
        msg = await self.send_message(
            to_agent_id, to_inbound_topic, "ping",
            mirror_node_url=mirror_node_url,
        )
        return msg is not None

    async def send_data_request(
        self,
        to_agent_id: str,
        to_inbound_topic: str,
        provider_id: str,
        params: dict[str, Any],
        mirror_node_url: str = "https://testnet.mirrornode.hedera.com",
    ) -> AgentMessage | None:
        """Envía una solicitud de datos a otro agente."""
        return await self.send_message(
            to_agent_id, to_inbound_topic, "data_request",
            payload={"provider_id": provider_id, "params": params},
            mirror_node_url=mirror_node_url,
        )

    def _log_message(self, direction: str, msg: AgentMessage):
        self._message_log.append({
            "direction": direction,
            "action": msg.action,
            "from": msg.from_agent_id,
            "to": msg.to_agent_id,
            "timestamp": msg.timestamp,
            "correlation_id": msg.correlation_id,
        })
        if len(self._message_log) > 1000:
            self._message_log = self._message_log[-500:]

    def get_message_log(self, limit: int = 50) -> list[dict]:
        return self._message_log[-limit:]

    def get_stats(self) -> dict:
        return {
            "total_messages": len(self._message_log),
            "sent": sum(1 for m in self._message_log if m["direction"] == "sent"),
            "received": sum(1 for m in self._message_log if m["direction"] == "received"),
            "pending_responses": len(self._pending_responses),
        }


agent_messaging: AgentMessaging | None = None
