<div align="center">

# 🤖 HashA2A 
## *The Agent-to-Agent Intelligence Layer*

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Hedera](https://img.shields.io/badge/Hedera-HCS%20|%20HIP--991-00B4D8?logo=hedera&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![A2A](https://img.shields.io/badge/A2A-Compliant-8B5CF6)
![MCP](https://img.shields.io/badge/MCP-10%20Tools-3B82F6)
![License](https://img.shields.io/badge/license-MIT-F7DF1E)
![Tests](https://img.shields.io/badge/tests-73%2F73-brightgreen)

---

> **HashA2A** is a decentralized **agent-to-agent data marketplace** where AI agents buy verified multi-oracle intelligence via **HBAR (HIP-991)** or **USDC (x402/AP2)** micropayments.

---

</div>

## Features

| Feature | Description |
|---------|-------------|
| 🔮 **OracleHub** | Multi-oracle price aggregation from **Pyth**, **CoinGecko**, and **Chainlink** (via DeFiLlama) — median with IQR confidence intervals |
| 📊 **Arbitrage Engine** | Real-time cross-oracle spread detection. Buy from the cheapest oracle, sell to the most expensive |
| 🔌 **A2A Protocol** | Full **Google A2A** compliance — JSON-RPC 2.0, SSE streaming, task lifecycle, context passing, AP2 mandates |
| 🛠️ **MCP Server** | 10 Model Context Protocol tools for Claude, Cursor, and any MCP-compatible agent |
| 🧠 **AI Analysis** | LangChain + OpenAI (GPT-5-nano) for deep market analysis |
| 🔍 **Deep Research** | Web search + news + social signals + prediction markets + AI |
| 💳 **x402 + AP2** | USDC payments via x402 HTTP 402 and AP2 cryptographic mandates with spending limits |
| 🔐 **JWT Auth** | Ephemeral tokens (60s-3600s TTL) with scope-based authorization |
| 🎯 **Prediction Markets** | Polymarket, Kalshi, PredictIt, Manifold — cross-validated probabilities |
| 📈 **Dashboards** | Live oracle prices, spread history charts, A2A task management, context activity |
| 🐳 **Docker** | One-command deployment with docker-compose |

## Architecture

```
Agent Client (Claude, LangChain, Google A2A, MCP)
       │
       ├── MCP  ───── http://localhost:8080/mcp
       ├── A2A  ───── http://localhost:8080/api/v1/a2a/rpc
       ├── SSE  ───── http://localhost:8080/api/v1/a2a/rpc/stream
       ├── REST ───── http://localhost:8080/api/v1/...
       └── Agent Card ── http://localhost:8080/.well-known/agent.json
                              │
 ┌─────────────────────────────────────────────┐
 │               HashA2A Core                    │
 │                                               │
 │  OracleHub  ─── Pyth · CoinGecko · DeFiLlama │
 │  Arbitrage  ─── Spread detection + ranking    │
 │  Research   ─── Web + News + AI Analysis     │
 │  TaskManager ─ A2A lifecycle + artifacts     │
 │  ContextManager ─ Context IDs + summaries    │
 │  PaymentEngine ─ HIP-991 + x402 + AP2        │
 │  AuthService ── JWT + Mandates               │
 │  ConsensusLogger ─ HCS audit trail           │
 └─────────────────────────────────────────────┘
```

## Pricing

USDC prices are **fixed**. HBAR prices update in **real-time** from CoinGecko.

| Product | USDC | HBAR (approx) |
|---------|------|---------------|
| Price Feed (single asset, multi-oracle) | $0.25 | ≈ 2.8 HBAR |
| Arbitrage Scan (all assets) | $0.50 | ≈ 5.5 HBAR |
| Deep Research (web + news + AI) | $0.50 | ≈ 5.5 HBAR |
| Prediction Market (per provider) | $0.15 | ≈ 1.7 HBAR |
| Aggregate Intelligence | $1.00 | ≈ 11.1 HBAR |

## A2A Protocol Compliance

HashA2A implements the **Agent-to-Agent (A2A) protocol** governed by the Linux Foundation:

### Agent Card
Served at `/.well-known/agent.json`:
- 5 skills with formal JSON Schema input/output definitions
- JSON-RPC 2.0 + SSE streaming interfaces
- JWT + no-auth authentication schemes
- AP2 mandate support
- Context passing and artifact storage

### JSON-RPC 2.0 Methods

| Method | RPC Endpoint | Description |
|--------|-------------|-------------|
| `message/send` | `/api/v1/a2a/rpc` | Create and process a task |
| `message/stream` | `/api/v1/a2a/rpc/stream` | Create task with SSE real-time updates |
| `tasks/get` | `/api/v1/a2a/rpc` | Get task state and result |
| `tasks/list` | `/api/v1/a2a/rpc` | List tasks with filter |
| `tasks/cancel` | `/api/v1/a2a/rpc` | Cancel a running task |

### Task Lifecycle

```
submitted → working → input-required → completed
                     → failed / canceled / rejected
```

### Context Passing

- `contextId` groups multiple interactions under the same workflow
- `ContextSummary` passes antecedents without sharing full memory
- `fork_context()` creates branching conversations with inherited history

## MCP Tools (10)

| Tool | Description |
|------|-------------|
| `list_providers` | List prediction market providers |
| `get_market_data` | Request data from a provider |
| `check_request` | Poll request result |
| `get_agent_profile` | View agent identity |
| `analyze_market` | AI analysis of market data |
| `deep_research` | Full web+news+AI research |
| `aggregate_market_data` | Multi-provider intelligence |
| `verified_feed` | Cross-validated price feed |
| `get_price` | Multi-oracle price (Pyth+CoinGecko+Chainlink) |
| `scan_arbitrage` | Cross-oracle arbitrage opportunities |

## Quick Start

```bash
# Docker (recommended)
docker compose up -d
curl http://localhost:8080/api/v1/agent/health

# Or Python directly
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your credentials
python runner.py
```

## API Endpoints

### Feeds & Data
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/feeds/prices` | Multi-oracle price feed |
| POST | `/api/v1/feeds/arbitrage` | Cross-oracle arbitrage scan |
| GET | `/api/v1/feeds/pricing` | Real-time pricing (USDC + HBAR) |
| GET | `/api/v1/feeds/x402/manifest` | x402 payment manifest |

### A2A Tasks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/a2a/rpc` | JSON-RPC 2.0 (message/send, tasks/get, etc.) |
| POST | `/api/v1/a2a/rpc/stream` | SSE streaming RPC |
| POST | `/api/v1/tasks` | Create task (REST) |
| GET | `/api/v1/tasks/{id}` | Get task |
| GET | `/api/v1/tasks` | List tasks |
| POST | `/api/v1/tasks/{id}/complete` | Complete task with artifact |
| POST | `/api/v1/tasks/{id}/artifacts` | Upload artifact |
| GET | `/api/v1/tasks/{id}/artifacts` | List artifacts |
| POST | `/api/v1/tasks/context` | Create context |
| GET | `/api/v1/tasks/context/{id}/summary` | Context summary |
| POST | `/api/v1/tasks/context/{id}/fork` | Fork context |

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/token` | Request ephemeral JWT |
| POST | `/api/v1/auth/verify` | Verify Bearer token |
| POST | `/api/v1/auth/mandates` | Create AP2 mandate |
| POST | `/api/v1/auth/mandates/{id}/authorize` | Authorize spending |

### Prediction Markets
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/requests` | Buy prediction data |
| POST | `/api/v1/requests/aggregate` | Multi-provider aggregation |
| POST | `/api/v1/research` | Deep research |

### Agent Discovery
| Path | Description |
|------|-------------|
| `/.well-known/agent.json` | A2A Agent Card |
| `/.well-known/x402.json` | x402 payment manifest |
| `/llms.txt` | LLM-readable docs |
| `/mcp/` | MCP server info |

### Dashboards
| Path | Description |
|------|-------------|
| `/` | Landing page with live BTC price |
| `/dashboard` | Main dashboard |
| `/dashboard/oracles` | Oracle prices + spread history charts |
| `/dashboard/tasks` | A2A task management dashboard |

## Oracle Sources

| Source | Assets | Cost | Type |
|--------|--------|------|------|
| **Pyth Hermes** | BTC, ETH, SOL, XAU, XAG, USD/JPY | Free | First-party institutions |
| **CoinGecko** | 17 crypto assets | Free | CEX/DEX aggregation |
| **DeFiLlama** | BTC, ETH, SOL | Free | Chainlink via DeFiLlama |

## Tech Stack

- **Python 3.12** + **FastAPI** + **Uvicorn**
- **Hiero SDK** (Hedera HCS + HIP-991)
- **MCP** (Model Context Protocol, 10 tools)
- **A2A** (Google Agent-to-Agent protocol)
- **LangChain** + **OpenAI** (GPT-5-nano / GPT-5.5)
- **x402** + **AP2** (USDC payments on Base)
- **Docker** + **Docker Compose**
- **Chart.js** (dashboards)
- **HyperFrames** (promo video)

## License

MIT — Use it, fork it, sell data with it.
