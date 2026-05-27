# 🤖 HashA2A — The Agent-to-Agent Intelligence Layer

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Hedera](https://img.shields.io/badge/Hedera-Mainnet-00B4D8?logo=hedera&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![A2A](https://img.shields.io/badge/A2A-Compliant-8B5CF6)
![MCP](https://img.shields.io/badge/MCP-19%20Tools-3B82F6)
![License](https://img.shields.io/badge/license-MIT-F7DF1E)
![Tests](https://img.shields.io/badge/tests-115%2F115-brightgreen)

> **HashA2A** is a decentralized **agent-to-agent data marketplace** running on **Hedera mainnet**. AI agents buy verified multi-oracle intelligence via **HBAR (HIP-991)** or **USDC (x402/AP2)** micropayments.

## What it does

- **Multi-oracle prices** — 36 assets across 5 sources (Pyth, CoinGecko, Binance, DeFiLlama, ForexAPI). Median with IQR confidence intervals.
- **Prediction markets** — 5 providers (Polymarket, Kalshi, PredictIt, Manifold, Hyperliquid). Cross-validated probabilities.
- **Arbitrage scanning** — Real-time cross-oracle spread detection across all assets, ranked by opportunity.
- **Deep research** — Web search + news + social signals + prediction markets + AI analysis (LangChain + GPT-5-nano).
- **Enterprise plugin** — Hedera Agent Kit bridge with 6 tools: account balance, transfers, topic management, account info.

## Built for

AI agents, trading bots, DeFi protocols, and enterprise teams that need verified, cross-validated market data with on-chain payment rails.

## Connect

- **Server URL:** `https://hasha2a.com/mcp`
- **Auth:** HBAR (HIP-991 auto-fees) or USDC (x402/Circle Gateway, gasless)
- **Transport:** Streamable HTTP (remote) or stdio via `mcp-remote`
- **Install:** `npx hasha2a-mcp-client add`

## Trust

- **19 MCP tools**, 5 oracle sources (36 assets), 5 prediction market providers
- **115 tests passing**, mainnet live on **Hedera**
- **HIP-991** fee collection, **HIP-1261** simple fees
- **x402 6-rule verification**: layout, amount, fee payer, signature, nonce, asset

## Links

- Docs: [github.com/ymiydev-prog/HashA2A](https://github.com/ymiydev-prog/HashA2A)
- Agent Card: [hasha2a.com/.well-known/agent.json](https://hasha2a.com/.well-known/agent.json)
- OpenAPI: [hasha2a.com/openapi.json](https://hasha2a.com/openapi.json)
- Install Script: [raw.githubusercontent.com/.../install-mcp.sh](https://raw.githubusercontent.com/ymiydev-prog/HashA2A/main/scripts/install-mcp.sh)

---

## Features

| Feature | Description |
|---------|-------------|
| 🔮 **OracleHub v2** | 36 assets × 5 sources — Pyth, CoinGecko, DeFiLlama, Binance, ForexAPI. Median with IQR confidence intervals |
| 📊 **Arbitrage Engine** | Real-time cross-oracle spread detection across all 36 assets |
| 🔌 **A2A Protocol** | Full **Google A2A** compliance — JSON-RPC 2.0, SSE streaming, task lifecycle, context passing, AP2 mandates |
| 🛠️ **MCP Server** | 18 Model Context Protocol tools — available via **Smithery** registry or one-command install |
| 🧠 **AI Analysis** | LangChain + OpenAI (GPT-5-nano) for deep market analysis |
| 🔍 **Deep Research** | Web search + news + social signals + prediction markets + AI |
| 💳 **x402 Triple Rail** | USDC on Base + HBAR/HTS on Hedera + **Circle Gateway** (gasless USDC via Agent Wallet, **6/6 verification rules**: layout, amount, fee payer safety, signature, nonce, asset) |
| 🔐 **JWT Auth** | Ephemeral tokens (60s-3600s TTL) with scope-based authorization |
| 🎯 **Prediction Markets** | Polymarket, Kalshi, PredictIt, Manifold, Hyperliquid — cross-validated probabilities |
| ⭐ **Quality Evaluation** | Auto-score every provider response — latency, completeness, accuracy, outlier detection |
| 🏢 **Enterprise Plugin** | Isolated `hedera-agent-kit` bridge — 6 additional MCP tools for account/topic/tx management |
| 📈 **Dashboards** | Live oracle prices, spread history, A2A tasks, **wallet balance/transactions** |
| 🔄 **Reverse Auctions** | Providers bid on requests — agents get the best price/quality |
| 🥩 **Staking & Slashing** | Provider reputation with stake-based slashing for bad data |
| 💚 **Health Checks** | Live API health indicators (green/red) per provider — auto-detects outages |
| 🐳 **Docker** | One-command deployment with docker-compose → **mainnet live** |

## Quick Start

```bash
# One command — any agent, any machine
npx hasha2a-mcp-client add

# Or via shell script (no Node.js needed)
curl -fsSL https://raw.githubusercontent.com/ymiydev-prog/HashA2A/main/scripts/install-mcp.sh | bash

# Or run the server locally
docker compose up -d
curl http://localhost:8080/api/v1/agent/health
```

## Architecture

```
Agent Client (Claude, LangChain, Google A2A, MCP)
       │
        ├── MCP  ───── http://localhost:8080/mcp        (19 tools)
       ├── A2A  ───── http://localhost:8080/api/v1/a2a/rpc
       ├── SSE  ───── http://localhost:8080/api/v1/a2a/rpc/stream
       ├── REST ───── http://localhost:8080/api/v1/...
       └── Agent Card ── http://localhost:8080/.well-known/agent.json
                              │
 ┌─────────────────────────────────────────────────────┐
 │                  HashA2A Core                        │
 │                                                      │
 │  OracleHub  ─── Pyth · CoinGecko · DeFiLlama        │
 │                 Binance · ForexAPI (36 assets)       │
 │  Arbitrage  ─── Spread detection + ranking           │
 │  QualityEval ── Latency · completeness · accuracy    │
 │  Research   ─── Web + News + AI Analysis             │
 │  TaskManager ── A2A lifecycle + artifacts            │
 │  ContextManager ── Context IDs + summaries           │
 │  PaymentEngine ── HIP-991 + x402 + AP2               │
 │  AuthService ── JWT + Mandates                       │
 │  AuctionEngine ── Reverse auctions for best price    │
 │  StakingManager ── Provider stake + slashing         │
 │  ConsensusLogger ── HCS audit trail                  │
 │  x402Handler  ── 6-rule verification                 │
 └─────────────────────────────────────────────────────┘
       │
 ┌──────┴──────┐
 │  Plugin      │
 │  Bridge      │
 │  (isolated   │
 │   venv for   │
 │agent-kit)    │
 └──────────────┘
```

## MCP — Model Context Protocol

### Installation

**npm (recommended)** — auto-detects Claude Desktop, Cursor, Windsurf:
```bash
npx hasha2a-mcp-client add
# Or with a remote server URL
npx hasha2a-mcp-client add --url https://hasha2a.com/mcp
```

**Shell script** — no Node.js needed:
```bash
curl -fsSL https://raw.githubusercontent.com/ymiydev-prog/HashA2A/main/scripts/install-mcp.sh | bash
```

**via Smithery**: Published at `smithery.ai` — search "HashA2A".

**Manual** — add to your MCP client config:
```json
{
  "mcpServers": {
    "hasha2a": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://hasha2a.com/mcp"]
    }
  }
}
```

### Tools (19)

#### Oracle & Data
| Tool | Description |
|------|-------------|
| `get_price` | Multi-oracle price (Pyth+CoinGecko+Binance+DeFiLlama) |
| `list_assets` | List all 36 supported assets with metadata |
| `get_asset_profile` | Detailed info per asset — sources, change_24h, volume |
| `scan_arbitrage` | Cross-oracle arbitrage opportunities across all assets |
| `verified_feed` | Cross-validated price feed with confidence intervals |

#### Prediction Markets & Research
| Tool | Description |
|------|-------------|
| `list_providers` | List prediction market providers |
| `get_market_data` | Request data from a provider |
| `check_request` | Poll request result |
| `get_agent_profile` | View agent identity |
| `aggregate_market_data` | Multi-provider intelligence |
| `analyze_market` | AI analysis of market data |
| `deep_research` | Full web+news+AI research |

#### Enterprise Plugin (Hedera Agent Kit)
| Tool | Description |
|------|-------------|
| `kit_setup` | Setup isolated hedera-agent-kit environment |
| `kit_account_balance` | Get HBAR balance of any account |
| `kit_transfer_hbar` | Transfer HBAR to another account |
| `kit_create_topic` | Create an HCS topic |
| `kit_submit_message` | Submit message to HCS topic |
| `kit_topic_messages` | Get messages from HCS topic (Mirror Node) |
| `kit_get_account_info` | Get detailed account information |

## AI Agent SKILL

HashA2A provides a universal **SKILL** file that teaches any AI agent how to use the platform — endpoints, tools, pricing, payment rails, and workflows — without pasting documentation.

### Installation

**Via skills.sh (any agent — Claude Code, Gemini CLI, Codex CLI):**
```bash
npx skills add ymiydev-prog/HashA2A --skill hasha2a -g -y
```

**Via GitHub (manual):**
```bash
git clone https://github.com/ymiydev-prog/HashA2A.git ~/.claude/skills/hasha2a
```

Source: [`skills/hasha2a/SKILL.md`](skills/hasha2a/SKILL.md) + [`skills/hasha2a/references/core.md`](skills/hasha2a/references/core.md)

### AI Prompts

Copy-paste ready prompts at [`docs/ai-prompts.md`](docs/ai-prompts.md) — 15 prompts covering all 19 MCP tools, REST API, payment flows, and Hedera operations.

## IDE Setup

### ChatGPT (Developer Mode)
1. Open **Developer Mode** in ChatGPT
2. Go to **Custom MCP Connector**
3. Add the HashA2A MCP URL: `http://localhost:8080/mcp`
4. Or use GPT Actions: add OpenAPI spec at `/openapi.json`

### Claude.ai (claude.ai Pro/Team)
1. Go to **Settings → Capabilities → Add Connector**
2. Set URL to `http://localhost:8080/mcp`
3. Alternatively, upload the SKILL at `claude.ai/customize/skills`:
   - Download: [skills.zip](https://github.com/ymiydev-prog/HashA2A/archive/refs/heads/main.zip)
   - Upload the zip at `claude.ai/customize/skills`
   - Add `localhost:8080` to domain allowlist at `claude.ai/settings/capabilities`

### Claude Code (Terminal)
```bash
# Via npm package (auto-detects Claude Code)
npx hasha2a-mcp-client add

# Via SKILL
npx skills add ymiydev-prog/HashA2A --skill hasha2a -g -y
```

### Cursor
```bash
npx hasha2a-mcp-client add
# Or manually add to .cursor/mcp.json:
# { "mcpServers": { "hasha2a": { "command": "npx", "args": ["-y", "mcp-remote", "https://hasha2a.com/mcp"] } } }
```

### Windsurf
```bash
npx hasha2a-mcp-client add
# Or manually add to .windsurf/mcp_config.json
```

### Gemini CLI
```bash
npx skills add ymiydev-prog/HashA2A --skill hasha2a -g -y
```

### Codex CLI
```bash
npx skills add ymiydev-prog/HashA2A --skill hasha2a -g -y
# Or clone to ~/.claude/skills/hasha2a (Codex shares the Claude skills directory)
```

### Visual Studio Code (VS Code)
Add to `.vscode/mcp.json` or VS Code MCP settings:
```json
{ "servers": { "hasha2a": { "command": "npx", "args": ["-y", "mcp-remote", "https://hasha2a.com/mcp"] } } }
```

## Pricing

USDC prices are **fixed**. HBAR prices update in **real-time** from Binance + CoinGecko fallback.

| Product | USDC | HBAR (live) |
|---------|------|-------------|
| Price Feed (single asset, multi-oracle) | $0.25 | ≈ 2.76 HBAR |
| Arbitrage Scan (all 36 assets) | $0.50 | ≈ 5.52 HBAR |
| Arbitrage Verify (single pair) | $0.10 | ≈ 1.10 HBAR |
| Deep Research (web + news + AI) | $0.50 | ≈ 5.52 HBAR |
| Prediction Market (per provider) | $0.15 | ≈ 1.66 HBAR |
| Aggregate Intelligence (all sources) | $1.00 | ≈ 11.05 HBAR |

> All transactions use **HIP-1261 Simple Fees**: `transaction_fee` is a MAX cap (0.05 HBAR basic, 0.1 HBAR for HIP-991). See [`docs/hip-1261-simple-fees.md`](docs/hip-1261-simple-fees.md).

## Oracle Sources — 36 Assets, 5 Sources

| Source | Assets | Cost | Type |
|--------|--------|------|------|
| **Pyth Hermes** | BTC, ETH, SOL, XAU, XAG, USD/JPY + equities (7) | Free | First-party institutions |
| **CoinGecko** | 17 crypto assets | Free | CEX/DEX aggregation |
| **DeFiLlama** | BTC, ETH, SOL (Chainlink via DeFiLlama) | Free | Chainlink data feed |
| **Binance** | BTC, ETH, SOL, BNB, XRP, ADA + more | Free | Centralized exchange |
| **ForexAPI** | EUR/USD, GBP/USD, AUD/USD, CAD/USD, CHF/USD, CNH/USD | Free | Open exchange rates |

### Asset Coverage

| Category | Count | Examples |
|----------|-------|---------|
| Crypto | 21 | BTC, ETH, SOL, HBAR, BNB, XRP, ADA, DOGE, AVAX, DOT, LINK, UNI, MATIC, LTC, AAVE, ATOM, ARB, APT, OP, SUI, PEPE |
| Equities | 7 | AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, META |
| Commodities | 2 | XAU (Gold), XAG (Silver) |
| Forex | 6 | EUR/USD, GBP/USD, AUD/USD, CAD/USD, CHF/USD, CNH/USD |

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

## Testing

```bash
# All tests (115 passing)
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
| `/mcp/` | MCP server info (GET) + Streamable HTTP (POST) |

### Dashboards
| Path | Description |
|------|-------------|
| `/` | Landing page with live BTC price |
| `/dashboard` | Main admin dashboard — provider cards, wallet, health status |
| `/dashboard/oracles` | Oracle prices + spread history charts |
| `/dashboard/tasks` | A2A task management dashboard |
| `/dashboard/wallet` | Wallet balance, USD equivalent, transactions |
| `/dashboard/health` | Provider health check API (JSON) |

## Quick Start (Local Dev)

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

## Tech Stack

- **Python 3.12** + **FastAPI** + **Uvicorn**
- **Hiero SDK 0.2.6** (Hedera HCS + HIP-991 + HIP-1261)
- **MCP** (Model Context Protocol, 19 tools)
- **A2A** (Google Agent-to-Agent protocol)
- **LangChain** + **OpenAI** (GPT-5-nano)
- **x402** (Base USDC + Hedera HBAR/HTS, 6-rule verification)
- **Hedera Agent Kit** (isolated plugin bridge)
- **pynacl** (ed25519 signature verification)
- **Docker** + **Docker Compose**
- **Chart.js** (dashboards)
- **HyperFrames** (promo video)
- **tweepy** (Twitter/X auto-promotion @hasha2a)

## Deployment

HashA2A runs on **Hedera mainnet** via Docker. The MCP server is discoverable through:

- **Smithery**: `smithery.ai` — search "HashA2A"
- **mcp.so**: Public MCP directory listing
- **Install script**: `curl -fsSL https://raw.githubusercontent.com/ymiydev-prog/HashA2A/main/scripts/install-mcp.sh | bash`

## Documentation

| Doc | Description |
|-----|-------------|
| [`skills/hasha2a/SKILL.md`](skills/hasha2a/SKILL.md) | Universal SKILL for AI agents (Claude Code, Gemini, Codex, etc.) |
| [`skills/hasha2a/references/core.md`](skills/hasha2a/references/core.md) | Tools, endpoints, pricing, assets, payment rails reference |
| [`docs/ai-prompts.md`](docs/ai-prompts.md) | 15 copy-paste prompts for agents |
| [`docs/hip-1261-simple-fees.md`](docs/hip-1261-simple-fees.md) | HIP-1261 transaction_fee max-cap explained |
| [`docs/hiero-sdk-compatibility.md`](docs/hiero-sdk-compatibility.md) | hiero-sdk-python 0.2.0 vs 0.2.6 migration |
| [`docs/client-examples.md`](docs/client-examples.md) | Integration examples (cURL, Python, LangChain) |
| [`scripts/x402_flow_fixture.py`](scripts/x402_flow_fixture.py) | Replayable x402 flow demonstration |

## License

MIT — Use it, fork it, sell data with it.
