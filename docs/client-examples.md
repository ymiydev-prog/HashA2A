# 🧪 Client Integration Examples

> Cómo un agente cliente (LangChain, Python, cURL) consume la API de HashA2A.

---

## 📦 cURL

```bash
# 1️⃣ List available providers
curl -s http://localhost:8080/api/v1/providers | jq

# 2️⃣ Request market data
curl -s -X POST http://localhost:8080/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{"provider_id": "polymarket", "params": {"query": "Bitcoin", "limit": 3}}'

# Response includes payment instructions:
# {
#   "request_id": "abc-123",
#   "payment": {
#     "amount_hbar": 0.5,
#     "destination_account": "0.0.1234567",
#     "memo": "HASHA2A:abc-123:polymarket"
#   }
# }

# 3️⃣ Poll for result (after sending HBAR)
curl -s http://localhost:8080/api/v1/requests/abc-123 | jq

# 4️⃣ View agent profile
curl -s http://localhost:8080/api/v1/agent/profile | jq
```

---

## 🐍 Python (httpx)

```python
import httpx
import time
import json

BASE = "http://localhost:8080/api/v1"

def request_data(provider: str, params: dict) -> dict:
    """Request data from HashA2A. Returns payment instructions."""
    resp = httpx.post(f"{BASE}/requests", json={
        "provider_id": provider,
        "params": params,
    })
    return resp.json()

def wait_for_result(request_id: str, timeout: int = 120) -> dict:
    """Poll until the request completes or times out."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = httpx.get(f"{BASE}/requests/{request_id}")
        result = resp.json()
        if result.get("status") == "completed":
            return result
        time.sleep(3)
    raise TimeoutError("Request did not complete in time")

# ---- Usage ----
payment = request_data("polymarket", {"query": "Ethereum", "limit": 5, "include_analysis": True})

print(f"📤 Send {payment['payment']['amount_hbar']} HBAR")
print(f"   To: {payment['payment']['destination_account']}")
print(f"   Memo: {payment['payment']['memo']}")

# After sending HBAR with the memo...
result = wait_for_result(payment["request_id"])

print(f"\n✅ Status: {result['status']}")
print(f"📊 Markets found: {result['data']['total_found']}")
print(f"🧠 Analysis:\n{result['analysis']}")
print(f"🔗 HCS Proof: {result['proof_tx_id']}")
```

---

## 🦜🔗 LangChain Agent

```python
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
import httpx
import time

BASE = "http://localhost:8080/api/v1"


@tool
def list_providers() -> str:
    """List all available data providers with prices."""
    resp = httpx.get(f"{BASE}/providers")
    providers = resp.json()
    return "\n".join(
        f"  • {p['name']} ({p['provider_id']}): {p['cost_hbar']} HBAR — trust: {p['trust_score']:.0f}/100"
        for p in providers
    )


@tool
def buy_polymarket_data(query: str, limit: int = 5) -> str:
    """Buy processed Polymarket data. Agent must have HBAR to pay."""
    resp = httpx.post(f"{BASE}/requests", json={
        "provider_id": "polymarket",
        "params": {"query": query, "limit": limit, "include_analysis": True},
    })
    data = resp.json()
    print(f"\n[PAYMENT REQUIRED] Send {data['payment']['amount_hbar']} HBAR to")
    print(f"  {data['payment']['destination_account']}")
    print(f"  with memo: {data['payment']['memo']}\n")

    # Simulate waiting for payment confirmation
    for _ in range(30):
        time.sleep(2)
        result = httpx.get(f"{BASE}/requests/{data['request_id']}").json()
        if result.get("status") == "completed":
            return f"Markets: {result['data']['total_found']} found\nAnalysis:\n{result['analysis']}"

    return "Payment not confirmed within timeout."


# Register as LangChain tools
tools = [list_providers, buy_polymarket_data]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
```

---

## 🤖 HCS-10 Agent (Hedera-native)

```python
# Discovering HashA2A via HCS-10 HOL Registry
from hedera import Client, TopicMessageQuery

client = Client.for_testnet()
client.set_operator(my_id, my_key)

# Subscribe to HOL registry topic to find HashA2A
HOL_REGISTRY = "0.0.29640405"

def on_registry_message(message):
    content = message.contents.decode()
    if "HashA2A" in content or "data-oracle" in content:
        print(f"🔍 Found HashA2A: {content}")
        # Extract inbound_topic and send a connection request

query = TopicMessageQuery().set_topic_id(HOL_REGISTRY)
query.subscribe(client, on_registry_message)
```

---

## 📡 WebSocket Polling (for real-time results)

```python
import asyncio
import httpx

async def request_and_await(provider: str, params: dict) -> dict:
    async with httpx.AsyncClient() as client:
        # Create request
        resp = await client.post(f"{BASE}/requests", json={
            "provider_id": provider, "params": params,
        })
        data = resp.json()
        request_id = data["request_id"]

        print(f"Awaiting payment: {data['payment']['memo']}")

        # Async poll
        for _ in range(60):
            await asyncio.sleep(2)
            resp = await client.get(f"{BASE}/requests/{request_id}")
            result = resp.json()
            if result.get("status") == "completed":
                return result

        raise TimeoutError("Timed out waiting for data")

result = asyncio.run(request_and_await("polymarket", {"query": "AI", "limit": 3}))
print(result["analysis"])
```

---

## ❌ Error Handling

| HTTP | Error | Cause |
|------|-------|-------|
| 404 | Unknown provider | `provider_id` doesn't exist |
| 402 | Insufficient HBAR | `max_cost_hbar < provider.cost_hbar` |
| 404 | Request expired | Payment not sent within TTL |
| 500 | Processing failed | Provider API or AI error |

```python
try:
    resp = httpx.post(f"{BASE}/requests", json={"provider_id": "invalid"})
    resp.raise_for_status()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        print(f"Provider not found: {e.response.json()['detail']}")
    elif e.response.status_code == 402:
        print(f"Payment required: {e.response.json()['detail']}")
```
