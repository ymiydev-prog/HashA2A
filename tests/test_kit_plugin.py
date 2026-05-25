"""Tests for the Hedera Agent Kit Plugin bridge."""
import json
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from plugins.hedera_kit_bridge import HederaKitPlugin


class MockPopen:
    """Simulate the bridge subprocess for testing."""

    def __init__(self):
        self.stdin = MagicMock()
        self.stdout = MagicMock()
        self.stderr = MagicMock()
        self.returncode = 0

    def terminate(self):
        pass

    def wait(self, timeout=5):
        pass


def make_mock_popen(responses: list | None = None):
    """Create a MockPopen with canned responses for _call()."""
    mp = MockPopen()

    def write_side_effect(data):
        pass

    def readline_side_effect():
        if responses and len(responses) > 0:
            resp = responses.pop(0)
            return json.dumps(resp) + "\n"
        return json.dumps({"id": 1, "result": None}) + "\n"

    mp.stdin.write.side_effect = write_side_effect
    mp.stdout.readline.side_effect = readline_side_effect
    return mp


class TestHederaKitPlugin:
    """Unit tests for HederaKitPlugin communication layer."""

    def setup_method(self):
        self.plugin = HederaKitPlugin(
            operator_id="0.0.12345",
            operator_key="302e020100300506032b657004220420" + "aabb" * 16,
            network="testnet",
        )

    def test_init_stores_credentials(self):
        assert self.plugin.operator_id == "0.0.12345"
        assert self.plugin.operator_key is not None
        assert self.plugin.network == "testnet"
        assert not self.plugin._ready
        assert self.plugin._process is None

    @patch("plugins.hedera_kit_bridge.PLUGIN_DIR")
    def test_is_setup_checks_venv_python(self, mock_plugindir):
        mock_bin = MagicMock(spec=Path)
        mock_python = MagicMock(spec=Path)
        mock_python.exists.return_value = True
        mock_bin.__truediv__.return_value = mock_python
        mock_plugindir.__truediv__.return_value = mock_bin
        assert self.plugin.is_setup is True

    @patch("plugins.hedera_kit_bridge.PLUGIN_DIR")
    def test_is_setup_checks_venv_not_exists(self, mock_plugindir):
        mock_bin = MagicMock(spec=Path)
        mock_python = MagicMock(spec=Path)
        mock_python.exists.return_value = False
        mock_bin.__truediv__.return_value = mock_python
        mock_plugindir.__truediv__.return_value = mock_bin
        assert self.plugin.is_setup is False

    @patch("subprocess.Popen")
    def test_call_sends_json_and_parses_response(self, mock_popen):
        mp = make_mock_popen([
            {"id": 1, "result": {"balance": {"hbars": 100.0}}},
        ])
        mock_popen.return_value = mp

        self.plugin._process = mp
        self.plugin._ready = True

        result = self.plugin._call("get_account_balance", {"account_id": "0.0.12345"})
        assert result == {"balance": {"hbars": 100.0}}
        mp.stdin.write.assert_called_once()
        assert "get_account_balance" in mp.stdin.write.call_args[0][0]

    @patch("subprocess.Popen")
    def test_call_raises_on_error_response(self, mock_popen):
        mp = make_mock_popen([
            {"id": 1, "error": "Something went wrong"},
        ])
        mock_popen.return_value = mp

        self.plugin._process = mp
        self.plugin._ready = True

        with pytest.raises(RuntimeError, match="Something went wrong"):
            self.plugin._call("ping")

    def test_call_raises_if_not_running(self):
        with pytest.raises(RuntimeError, match="not running"):
            self.plugin._call("ping")

    @patch("subprocess.Popen")
    @pytest.mark.asyncio
    async def test_get_account_balance_async(self, mock_popen):
        mp = make_mock_popen([
            {"id": 1, "result": {"balance": {"hbars": 42.0}}},
        ])
        mock_popen.return_value = mp
        self.plugin._process = mp
        self.plugin._ready = True

        result = await self.plugin.get_account_balance("0.0.12345")
        assert result == {"balance": {"hbars": 42.0}}

    @patch("subprocess.Popen")
    @pytest.mark.asyncio
    async def test_async_methods_delegate_to_call(self, mock_popen):
        """All async methods should route through _call with correct params."""
        mp = make_mock_popen([
            {"id": 1, "result": "ok"},
            {"id": 2, "result": "topic_ok"},
            {"id": 3, "result": "msg_ok"},
        ])
        mock_popen.return_value = mp
        self.plugin._process = mp
        self.plugin._ready = True

        r1 = await self.plugin.transfer_hbar("0.0.9999", 50)
        assert r1 == "ok"

        r2 = await self.plugin.create_topic("test memo")
        assert r2 == "topic_ok"

        r3 = await self.plugin.submit_message("0.0.8888", "hello")
        assert r3 == "msg_ok"

    @patch("subprocess.Popen")
    @pytest.mark.asyncio
    async def test_get_topic_messages(self, mock_popen):
        mp = make_mock_popen([
            {"id": 1, "result": [{"sequence_number": 1}, {"sequence_number": 2}]},
        ])
        mock_popen.return_value = mp
        self.plugin._process = mp
        self.plugin._ready = True

        result = await self.plugin.get_topic_messages("0.0.7777", 5)
        assert len(result) == 2
        assert result[0]["sequence_number"] == 1

    def test_stop_terminates_process(self):
        mp = MagicMock()
        self.plugin._process = mp
        self.plugin._ready = True

        self.plugin.stop()
        mp.terminate.assert_called_once()
        mp.wait.assert_called_once_with(timeout=5)
        assert self.plugin._process is None
        assert not self.plugin._ready
