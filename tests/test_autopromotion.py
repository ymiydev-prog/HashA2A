import sys
import os
import pytest
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestAgentDirectory:
    def test_add_agent(self):
        from core.agent_directory import AgentDirectory
        d = AgentDirectory()
        agent = d.add_or_update({
            "agent_id": "0.0.123",
            "agent_name": "TestAgent",
            "description": "A test agent",
            "tags": ["test", "ai"],
            "inbound_topic": "0.0.456",
            "outbound_topic": "0.0.789",
            "treasury_account": "0.0.123",
            "supported_chains": ["hedera"],
        })
        assert agent.agent_name == "TestAgent"
        assert agent.presence == "online"
        assert d.count == 1

    def test_update_agent(self):
        from core.agent_directory import AgentDirectory
        d = AgentDirectory()
        d.add_or_update({"agent_id": "0.0.123", "agent_name": "TestAgent", "treasury_account": "0.0.123"})
        d.add_or_update({"agent_id": "0.0.123", "agent_name": "UpdatedAgent", "treasury_account": "0.0.123"})
        assert d.count == 1
        agent = d.get("0.0.123")
        assert agent.agent_name == "UpdatedAgent"
        assert agent.heartbeat_count == 2

    def test_list_online(self):
        from core.agent_directory import AgentDirectory
        d = AgentDirectory()
        d.add_or_update({"agent_id": "0.0.1", "agent_name": "A1", "treasury_account": "0.0.1"})
        d.add_or_update({"agent_id": "0.0.2", "agent_name": "A2", "treasury_account": "0.0.2"})
        assert len(d.list_online()) == 2

    def test_update_presence(self):
        from core.agent_directory import AgentDirectory
        d = AgentDirectory()
        d.add_or_update({"agent_id": "0.0.1", "agent_name": "A1", "treasury_account": "0.0.1"})
        d.update_presence("0.0.1", "offline")
        assert d.get("0.0.1").presence == "offline"

    def test_stats(self):
        from core.agent_directory import AgentDirectory
        d = AgentDirectory()
        d.add_or_update({"agent_id": "0.0.1", "agent_name": "A1", "treasury_account": "0.0.1"})
        stats = d.get_stats()
        assert stats["total_agents"] == 1
        assert stats["online_agents"] == 1

    def test_remove(self):
        from core.agent_directory import AgentDirectory
        d = AgentDirectory()
        d.add_or_update({"agent_id": "0.0.1", "agent_name": "A1", "treasury_account": "0.0.1"})
        assert d.remove("0.0.1")
        assert d.count == 0


class TestHandshake:
    def test_initiate_connection(self):
        from core.protocols.handshake import HandshakeManager, HandshakeState
        hm = HandshakeManager()
        msg = hm.initiate_connection("agent_a", "Agent A", "agent_b")
        assert msg.action == "connect"
        assert msg.from_agent_id == "agent_a"
        assert msg.to_agent_id == "agent_b"
        state = hm.get_connection_state("agent_a", "agent_b")
        assert state == HandshakeState.INITIATED

    def test_respond_ack(self):
        from core.protocols.handshake import HandshakeManager, HandshakeState
        hm = HandshakeManager()
        ack = hm.respond_ack("agent_b", "Agent B", "agent_a")
        assert ack.action == "ack"
        state = hm.get_connection_state("agent_a", "agent_b")
        assert state == HandshakeState.CONNECTED

    def test_respond_reject(self):
        from core.protocols.handshake import HandshakeManager, HandshakeState
        hm = HandshakeManager()
        reject = hm.respond_reject("agent_b", "Agent B", "agent_a", "Not interested")
        assert reject.action == "reject"
        state = hm.get_connection_state("agent_a", "agent_b")
        assert state == HandshakeState.REJECTED

    def test_close_connection(self):
        from core.protocols.handshake import HandshakeManager, HandshakeState
        hm = HandshakeManager()
        hm.initiate_connection("agent_a", "Agent A", "agent_b")
        hm.respond_ack("agent_b", "Agent B", "agent_a")
        close = hm.close_connection("agent_a", "agent_b")
        assert close.action == "close"
        state = hm.get_connection_state("agent_a", "agent_b")
        assert state == HandshakeState.CLOSED

    def test_message_serialization(self):
        from core.protocols.handshake import HandshakeMessage
        msg = HandshakeMessage(
            action="connect",
            from_agent_id="a",
            from_agent_name="A",
            to_agent_id="b",
        )
        json_str = msg.to_json()
        restored = HandshakeMessage.from_json(json_str)
        assert restored.action == msg.action
        assert restored.from_agent_id == msg.from_agent_id


class TestAgentMessaging:
    def test_create_message(self):
        from core.agent_messaging import AgentMessage
        msg = AgentMessage(
            action="ping",
            from_agent_id="a",
            from_agent_name="A",
            to_agent_id="b",
        )
        assert msg.type == "message"
        assert msg.action == "ping"
        assert msg.correlation_id

    def test_message_serialization(self):
        from core.agent_messaging import AgentMessage
        msg = AgentMessage(
            action="data_request",
            from_agent_id="a",
            from_agent_name="A",
            to_agent_id="b",
            payload={"provider_id": "polymarket"},
        )
        json_str = msg.to_json()
        restored = AgentMessage.from_json(json_str)
        assert restored.action == msg.action
        assert restored.payload == msg.payload

    def test_register_handler(self):
        from core.agent_messaging import AgentMessaging
        am = AgentMessaging("agent_a", "Agent A")
        async def handler(msg):
            return None
        am.register_handler("ping", handler)
        assert "ping" in am._handlers

    def test_get_stats(self):
        from core.agent_messaging import AgentMessaging
        am = AgentMessaging("agent_a", "Agent A")
        stats = am.get_stats()
        assert "total_messages" in stats
        assert "sent" in stats
        assert "received" in stats


class TestAgentListener:
    def test_create_listener(self):
        from core.agent_listener import AgentListener
        listener = AgentListener(
            mirror_node_url="https://testnet.mirrornode.hedera.com",
            hol_registry_topic="0.0.29640405",
            agent_id="0.0.123",
        )
        assert listener.hol_topic == "0.0.29640405"
        assert listener.agent_id == "0.0.123"
        assert not listener._running
