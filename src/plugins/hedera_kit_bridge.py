"""
Hedera Agent Kit Plugin — bridge to hedera-agent-kit in isolated venv.

Since hedera-agent-kit requires hiero-sdk-python==0.2.0 (conflicts with
our 0.2.6), this plugin runs in a separate virtual environment and
communicates via JSON-RPC over stdin/stdout subprocess.
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).parent / ".kit_venv"
KIT_REQUIREMENTS = [
    "hiero-sdk-python==0.2.0",
    "hedera-agent-kit>=3.4.0",
]
BRIDGE_SCRIPT = """
import json, sys
from hedera_agent_kit import HederaAgentKit
kit = HederaAgentKit(
    "{operator_id}",
    "{operator_key}",
    "{network}",
)
for line in sys.stdin:
    try:
        req = json.loads(line.strip())
        method = req.get("method")
        params = req.get("params", {})
        rid = req.get("id", 0)

        if method == "get_account_balance":
            result = kit.get_account_balance(params.get("account_id"))
        elif method == "get_account_info":
            result = kit.get_account_info(params.get("account_id"))
        elif method == "transfer_hbar":
            result = kit.transfer_hbar(
                params.get("to"),
                params.get("amount"),
            )
        elif method == "create_topic":
            result = kit.create_topic(
                params.get("memo", ""),
            )
        elif method == "submit_message":
            result = kit.submit_message(
                params.get("topic_id"),
                params.get("message", ""),
            )
        elif method == "get_topic_messages":
            result = kit.get_topic_messages(
                params.get("topic_id"),
                params.get("limit", 10),
            )
        elif method == "ping":
            result = "pong"
        else:
            result = {"error": f"Unknown method: {method}"}

        print(json.dumps({"id": rid, "result": result}))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({"id": rid, "error": str(e)}))
        sys.stdout.flush()
"""


class HederaKitPlugin:
    def __init__(self, operator_id: str, operator_key: str, network: str = "testnet"):
        self.operator_id = operator_id
        self.operator_key = operator_key
        self.network = network
        self._process: subprocess.Popen | None = None
        self._ready = False

    @property
    def is_setup(self) -> bool:
        return (PLUGIN_DIR / "bin" / "python").exists()

    def setup(self):
        """Create isolated venv and install hedera-agent-kit."""
        if self.is_setup:
            print("Plugin venv already exists")
            return

        print(f"Creating plugin venv at {PLUGIN_DIR}...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(PLUGIN_DIR)],
            check=True, capture_output=True,
        )

        pip = str(PLUGIN_DIR / "bin" / "pip")
        for pkg in KIT_REQUIREMENTS:
            print(f"  Installing {pkg}...")
            subprocess.run(
                [pip, "install", pkg],
                check=True, capture_output=True,
            )

        print("Plugin setup complete")

    def start(self):
        """Start the bridge subprocess."""
        if not self.is_setup:
            raise RuntimeError("Plugin not set up. Call setup() first.")

        python = str(PLUGIN_DIR / "bin" / "python")
        script = BRIDGE_SCRIPT.format(
            operator_id=self.operator_id,
            operator_key=self.operator_key,
            network=self.network,
        )

        self._process = subprocess.Popen(
            [python, "-c", script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Verify it's running
        result = self._call("ping")
        self._ready = result == "pong"
        return self._ready

    def _call(self, method: str, params: dict | None = None) -> Any:
        """Send JSON-RPC call to bridge and get result."""
        if not self._process or not self._process.stdin:
            raise RuntimeError("Plugin not running")

        req = json.dumps({"method": method, "params": params or {}, "id": 1})
        self._process.stdin.write(req + "\n")
        self._process.stdin.flush()

        line = self._process.stdout.readline() if self._process.stdout else ""
        if not line:
            raise RuntimeError("No response from plugin")
        resp = json.loads(line.strip())
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp.get("result")

    async def get_account_balance(self, account_id: str) -> dict:
        return await asyncio.to_thread(self._call, "get_account_balance", {"account_id": account_id})

    async def get_account_info(self, account_id: str) -> dict:
        return await asyncio.to_thread(self._call, "get_account_info", {"account_id": account_id})

    async def transfer_hbar(self, to: str, amount: int) -> dict:
        return await asyncio.to_thread(self._call, "transfer_hbar", {"to": to, "amount": amount})

    async def create_topic(self, memo: str = "") -> dict:
        return await asyncio.to_thread(self._call, "create_topic", {"memo": memo})

    async def submit_message(self, topic_id: str, message: str) -> dict:
        return await asyncio.to_thread(self._call, "submit_message", {"topic_id": topic_id, "message": message})

    async def get_topic_messages(self, topic_id: str, limit: int = 10) -> list:
        return await asyncio.to_thread(self._call, "get_topic_messages", {"topic_id": topic_id, "limit": limit})

    def stop(self):
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None
            self._ready = False

    def __del__(self):
        self.stop()
