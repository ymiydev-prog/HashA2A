import time
import json
from enum import Enum
from typing import Any
from pydantic import BaseModel


class HandshakeState(str, Enum):
    INITIATED = "initiated"
    CONNECTED = "connected"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CLOSED = "closed"


class HandshakeMessage(BaseModel):
    type: str = "handshake"
    action: str  # "connect", "ack", "reject", "close"
    from_agent_id: str
    from_agent_name: str
    to_agent_id: str
    inbound_topic: str | None = None
    outbound_topic: str | None = None
    capabilities: list[str] = []
    message: str = ""
    timestamp: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "HandshakeMessage":
        data = json.loads(raw)
        return cls(**data)


class HandshakeManager:
    """
    Gestiona el protocolo de handshake HCS-10 entre agentes.
    Flujo:
      1. Agente A envía CONNECT a inbound topic de Agente B
      2. Agente B responde ACK a inbound topic de Agente A
      3. Conexión establecida — ambos agentes pueden intercambiar mensajes
    """

    def __init__(self):
        self._connections: dict[str, HandshakeState] = {}
        self._pending: dict[str, HandshakeMessage] = {}

    def initiate_connection(
        self,
        from_agent_id: str,
        from_agent_name: str,
        to_agent_id: str,
        capabilities: list[str] | None = None,
    ) -> HandshakeMessage:
        msg = HandshakeMessage(
            action="connect",
            from_agent_id=from_agent_id,
            from_agent_name=from_agent_name,
            to_agent_id=to_agent_id,
            capabilities=capabilities or [],
            message=f"Connection request from {from_agent_name}",
        )
        key = f"{from_agent_id}:{to_agent_id}"
        self._connections[key] = HandshakeState.INITIATED
        self._pending[key] = msg
        return msg

    def respond_ack(
        self,
        from_agent_id: str,
        from_agent_name: str,
        to_agent_id: str,
        inbound_topic: str | None = None,
        outbound_topic: str | None = None,
        capabilities: list[str] | None = None,
    ) -> HandshakeMessage:
        msg = HandshakeMessage(
            action="ack",
            from_agent_id=from_agent_id,
            from_agent_name=from_agent_name,
            to_agent_id=to_agent_id,
            inbound_topic=inbound_topic,
            outbound_topic=outbound_topic,
            capabilities=capabilities or [],
            message="Connection accepted",
        )
        key = f"{to_agent_id}:{from_agent_id}"
        self._connections[key] = HandshakeState.CONNECTED
        return msg

    def respond_reject(
        self,
        from_agent_id: str,
        from_agent_name: str,
        to_agent_id: str,
        reason: str = "Connection declined",
    ) -> HandshakeMessage:
        msg = HandshakeMessage(
            action="reject",
            from_agent_id=from_agent_id,
            from_agent_name=from_agent_name,
            to_agent_id=to_agent_id,
            message=reason,
        )
        key = f"{to_agent_id}:{from_agent_id}"
        self._connections[key] = HandshakeState.REJECTED
        return msg

    def close_connection(self, from_agent_id: str, to_agent_id: str) -> HandshakeMessage:
        msg = HandshakeMessage(
            action="close",
            from_agent_id=from_agent_id,
            from_agent_name="",
            to_agent_id=to_agent_id,
            message="Connection closed",
        )
        key = f"{from_agent_id}:{to_agent_id}"
        self._connections[key] = HandshakeState.CLOSED
        return msg

    def get_connection_state(self, from_agent_id: str, to_agent_id: str) -> HandshakeState:
        key = f"{from_agent_id}:{to_agent_id}"
        return self._connections.get(key, HandshakeState.INITIATED)

    def list_connections(self) -> dict[str, str]:
        return {k: v.value for k, v in self._connections.items()}


handshake_manager = HandshakeManager()
