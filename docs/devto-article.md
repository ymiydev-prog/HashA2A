---
title: "How to Connect Any AI Agent to Real-Time Oracle Data with 5 Lines of Code"
published: false
description: "HashA2A lets you plug AI agents into 36 multi-oracle assets, prediction markets, and arbitrage signals via MCP, A2A, or REST. Pay per query with HBAR or USDC. No subscription, no API key needed for reads."
tags: ["hedera", "ai-agents", "oracle", "mcp", "a2a", "web3", "micropayments"]
---

# How to Connect Any AI Agent to Real-Time Oracle Data with 5 Lines of Code

AI agents are useless without real data. But getting live prices, prediction markets, and arbitrage signals into an agent usually means: signing up for an API key, dealing with rate limits, paying a monthly subscription, and writing a custom integration.

HashA2A fixes this. It's a **serverless data marketplace** where AI agents pay per query — a few cents — and get back verified multi-oracle data. No API key. No monthly bill. One command to connect.

## What HashA2A Gives You

- **36 assets** across 5 oracle sources (Pyth, CoinGecko, DeFiLlama, Binance, ForexAPI)
- **4 prediction markets** (Polymarket, Kalshi, PredictIt, Manifold)
- **Cross-oracle arbitrage** — spot price differences between sources
- **Deep research** — web + news + social + AI analysis
- **A2A protocol** — full task lifecycle, SSE streaming, context passing

## Connect from Any MCP Client

### Claude Desktop

```bash
npx hasha2a-mcp-client add
```

Restart Claude. You'll see 18 new tools under the HashA2A server.

### Cursor / Windsurf

Same command — it auto-detects both.

```bash
npx hasha2a-mcp-client add
```

### Any MCP Agent (programmatic)

```python
import json, httpx

# Step 1: Initialize MCP session
r = httpx.post("http://localhost:8080/mcp", json={
    "jsonrpc": "2.0", "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18"}
})

# Step 2: Get price (5 lines of code — for real)
r = httpx.post("http://localhost:8080/mcp", json={
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {
        "name": "get_price",
        "arguments": {"asset": "BTC/USD"}
    }
})
print(r.json())
```

That's it. No auth headers. No API key setup. The MCP server returns:

```json
{
  "asset": "BTC/USD",
  "price": 87432.15,
  "sources": ["pyth", "coingecko", "defillama", "binance"],
  "median": 87450.0,
  "confidence": "high",
  "spread_pct": 0.08
}
```

## Pay Per Query (Not Per Month)

HashA2A uses **HIP-991** (HBAR native) and **x402** (USDC on Base) micropayments:

| Product | Price |
|---------|-------|
| Single asset price | $0.25 |
| Arbitrage scan (36 assets) | $0.50 |
| Deep research | $0.50 |
| Prediction market query | $0.15 |
| Aggregate intelligence | $1.00 |

All transactions use **HIP-1261 Simple Fees** — transaction fees are capped at 0.05 HBAR. Not the 5-10 HBAR default that most Hedera apps waste.

## Architecture in One Diagram

```
Agent → MCP (19 tools) → HashA2A → OracleHub (5 sources, 36 assets)
                                → Arbitrage Engine
                                → Deep Research (LangChain + OpenAI)
                                → Prediction Markets (5 providers)
                                → Hedera Agent Kit (6 tools)
```

## Available MCP Tools

**Oracle & Data**: `get_price`, `list_assets`, `get_asset_profile`, `scan_arbitrage`, `verified_feed`

**AI & Research**: `analyze_market`, `deep_research`

**Prediction Markets**: `list_providers`, `get_market_data`, `check_request`, `get_agent_profile`, `aggregate_market_data`

**Hedera Agent Kit**: `kit_setup`, `kit_account_balance`, `kit_transfer_hbar`, `kit_create_topic`, `kit_submit_message`, `kit_get_account_info`

## Connect Without MCP

HashA2A also speaks:

- **A2A (Agent-to-Agent)**: JSON-RPC 2.0 at `/api/v1/a2a/rpc` with SSE streaming
- **REST**: Full REST API at `/api/v1/...`
- **Agent Card**: Machine-readable at `/.well-known/agent.json`
- **n8n**: Install `hasha2a-n8n-nodes` from npm for drag-and-drop workflows

## Self-Host (Optional)

```bash
docker compose up -d
# → http://localhost:8080
# → MCP at /mcp/
# → REST at /api/v1/
```

## What's Next

- **Mainnet live**: Wallet `0.0.603064` on Hedera mainnet
- **Wallet dashboard**: Track balance and transactions in real-time
- **Quality scoring**: Every data provider is automatically scored on latency, completeness, and accuracy
- **Reverse auctions**: Providers bid on requests — agents get the best price

---

*HashA2A is open-source (MIT). Fork it, deploy it, sell data with it.*

**[GitHub →](https://github.com/ymiydev-prog/HashA2A)**
