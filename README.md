<div align="center">

# 🤖 HashA2A 
## *The Agent-to-Agent Intelligence Layer*

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Hedera](https://img.shields.io/badge/Hedera-HCS%20|%20HIP--991-00B4D8?logo=hedera&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![A2A](https://img.shields.io/badge/A2A-Compliant-8B5CF6)
![MCP](https://img.shields.io/badge/MCP-16%20Tools-3B82F6)
![License](https://img.shields.io/badge/license-MIT-F7DF1E)
![Tests](https://img.shields.io/badge/tests-100%2F100-brightgreen)

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
| 🛠️ **MCP Server** | 16 Model Context Protocol tools for Claude, Cursor, and any MCP-compatible agent |
| 🧠 **AI Analysis** | LangChain + OpenAI (GPT-5-nano) for deep market analysis |
| 🔍 **Deep Research** | Web search + news + social signals + prediction markets + AI |
| 💳 **x402 Dual Rail** | USDC on Base + HBAR/HTS on Hedera (exact scheme, **6/6 verification rules**: layout, amount, fee payer safety, signature, nonce, asset) |
| 🔐 **JWT Auth** | Ephemeral tokens (60s-3600s TTL) with scope-based authorization |
| 🎯 **Prediction Markets** | Polymarket, Kalshi, PredictIt, Manifold — cross-validated probabilities |
| 🏢 **Enterprise Plugin** | Isolated `hedera-agent-kit` bridge — 6 additional MCP tools for account/topic/tx management |
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
 ┌────────────────────────────────────────────┐
 │             HashA2A Core                     │
 │                                              │
 │  OracleHub  ─── Pyth · CoinGecko · DeFiLlama│
 │  Arbitrage  ─── Spread detection + ranking  │
 │  Research   ─── Web + News + AI Analysis    │
 │  TaskManager ─ A2A lifecycle + artifacts    │
 │  ContextManager ─ Context IDs + summaries   │
 │  PaymentEngine ─ HIP-991 + x402 + AP2       │
 │  AuthService ── JWT + Mandates              │
 │  ConsensusLogger ─ HCS audit trail          │
 │  x402Handler  ─ 6-rule verification         │
 └────────────────────────────────────────────┘
       │
 ┌──────┴──────┐
 │  Plugin      │
 │  Bridge      │
 │  (isolated   │
 │   venv for   │
 │agent-kit)    │
 └──────────────┘
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

> All fees use **HIP-1261 Simple Fees**: `transaction_fee` is a MAX cap (0.05 HBAR basic, 0.1 HBAR for HIP-991). See [`docs/hip-1261-simple-fees.md`](docs/hip-1261-simple-fees.md).

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

## MCP Tools (16)

### Oracle & Data
| Tool | Description |
|------|-------------|
| `list_providers` | List prediction market providers |
| `get_market_data` | Request data from a provider |
| `check_request` | Poll request result |
| `get_agent_profile` | View agent identity |
| `get_price` | Multi-oracle price (Pyth+CoinGecko+Chainlink) |
| `scan_arbitrage` | Cross-oracle arbitrage opportunities |
| `verified_feed` | Cross-validated price feed |
| `aggregate_market_data` | Multi-provider intelligence |
| `analyze_market` | AI analysis of market data |
| `deep_research` | Full web+news+AI research |

### Enterprise Plugin (Hedera Agent Kit)
| Tool | Description |
|------|-------------|
| `kit_setup` | Setup isolated hedera-agent-kit environment |
| `kit_account_balance` | Get HBAR balance of any account |
| `kit_transfer_hbar` | Transfer HBAR to another account |
| `kit_create_topic` | Create an HCS topic |
| `kit_submit_message` | Submit message to HCS topic |
| `kit_get_account_info` | Get detailed account information |

## x402 Hedera Rail — 6-Rule Verification

HashA2A implements the **exact scheme** for Hedera native payments (HIP-1261 compliant):

| # | Rule | What it checks |
|---|------|----------------|
| 1 | **Transaction layout** | feePayer matches transactionID.accountID |
| 2 | **Amount exactness** | Net amount to payTo matches expected |
| 3 | **Fee payer safety** | Fee payer is not a net sender |
| 4 | **Signature validity** | Ed25519 signatures in sigMap verify bodyBytes (via pynacl) |
| 5 | **Nonce (replay)** | accountID:transactionValidStart cache (1h TTL) |
| 6 | **Asset/token** | tokenTransfers validation for HTS tokens |

Replayable fixture (no secrets): `python scripts/x402_flow_fixture.py`
Full docs: [`docs/hiero-sdk-compatibility.md`](docs/hiero-sdk-compatibility.md)

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

# Or with custom port
PORT=8082 python runner.py
```

## Testing

```bash
# All tests
PYTHONPATH=src python -m pytest tests/ -v

# Smoke tests only (no credentials needed)
PYTHONPATH=src python -m pytest tests/ -m smoke -v

# E2E tests (requires .env)
PYTHONPATH=src python -m pytest tests/ -m e2e -v
```

## API Endpoints

### Feeds & Data
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/feeds/prices` | Multi-oracle price feed |
| POST | `/api/v1/feeds/arbitrage` | Cross-oracle arbitrage scan |
| GET | `/api/v1/feeds/pricing` | Real-time pricing (USDC + HBAR) |
| GET | `/api/v1/feeds/x402/manifest` | x402 payment manifest |
| POST | `/api/v1/feeds/x402/hedera/verify` | Verify HBAR/HTS payment |

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
| `/dashboard` | Main admin dashboard |
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
- **Hiero SDK 0.2.6** (Hedera HCS + HIP-991 + HIP-1261)
- **MCP** (Model Context Protocol, 16 tools)
- **A2A** (Google Agent-to-Agent protocol)
- **LangChain** + **OpenAI** (GPT-5-nano)
- **x402** (Base USDC + Hedera HBAR/HTS, 6-rule verification)
- **Hedera Agent Kit** (isolated plugin bridge)
- **pynacl** (ed25519 signature verification)
- **Docker** + **Docker Compose**
- **Chart.js** (dashboards)
- **HyperFrames** (promo video)
- **tweepy** (Twitter/X auto-promotion)

## Documentation

| Doc | Description |
|-----|-------------|
| [`docs/hip-1261-simple-fees.md`](docs/hip-1261-simple-fees.md) | HIP-1261 transaction_fee max-cap explained |
| [`docs/hiero-sdk-compatibility.md`](docs/hiero-sdk-compatibility.md) | hiero-sdk-python 0.2.0 vs 0.2.6 migration |
| [`docs/client-examples.md`](docs/client-examples.md) | Integration examples (cURL, Python, LangChain) |
| [`scripts/x402_flow_fixture.py`](scripts/x402_flow_fixture.py) | Replayable x402 flow demonstration |

## License

MIT — Use it, fork it, sell data with it.
