# HashA2A — Hedera AI Agent Bounty: Week 3 (MCP or x402 Agent)

## Project Name
**HashA2A** — Agent-to-Agent Intelligence Layer

## Project Summary
HashA2A is a decentralized data marketplace where AI agents discover, purchase, and consume verified multi-oracle intelligence. It implements both **MCP (Model Context Protocol)** and **x402 (pay-triggered execution)** — the exact combination this bounty targets.

### MCP Server (10 Tools)
- `list_providers` — Discovery of all registered data providers
- `get_market_data` — Fetch market data from any provider
- `get_price` — Multi-oracle price aggregation (Pyth, CoinGecko, DeFiLlama)
- `scan_arbitrage` — Cross-oracle spread detection
- `verified_feed` — Get verified data with confidence scoring
- `aggregate_market_data` — Aggregate across all oracles
- `deep_research` — Web search + AI analysis
- `check_request` — Check request status
- `get_agent_profile` — Agent discovery
- `analyze_market` — AI-powered market analysis

### x402 Payments (Dual Rail)
- **Rail 1: Base USDC** — USDC payments on Base network via x402.org facilitator
- **Rail 2: Hedera Native** — HBAR/HTS payments via Hedera `exact` scheme (HIP-1261 compliant)
  - Uses `TransferTransaction` partially signed, Base64 encoded
  - 6-rule verification: layout, amount exactness, fee payer safety, network correctness, transfer intent, replay protection
  - Fee estimation via mirror node `POST /api/v1/network/fees`

## Key Features
- **OracleHub**: Multi-oracle aggregation from 3 sources (Pyth, CoinGecko, DeFiLlama) — 19 assets
- **ArbitrageEngine**: Real-time cross-oracle spread detection
- **A2A Protocol**: Google A2A compliance — JSON-RPC 2.0, SSE streaming, 7-state task lifecycle
- **HIP-991**: Auto-collect fees on HCS topics
- **Simple Fees (HIP-1261)**: Optimized transaction fees (0.05-0.1 HBAR vs previous 5-10 HBAR)
- **MCP + A2A + REST**: Three integration paths for any agent
- **Agent Discovery**: `/.well-known/agent.json` card for autonomous discovery

## Hedera Agent Kit Integration
HashA2A uses `hedera-agent-kit` (Python) for Hedera blockchain operations alongside its custom MCP server implementation. The MCP server exposes Hedera tools (topic creation, message submission, account queries) through the standard MCP protocol, making them accessible to any MCP-compatible AI agent (Claude Desktop, Cursor, etc.).

### Architecture
```
AI Agent → MCP Client → HashA2A MCP Server → Hedera Agent Kit → Hedera Network
                                          → OracleHub (Pyth/CoinGecko/DeFiLlama)
                                          → ArbitrageEngine
                                          → x402 Handler (Base USDC + Hedera HBAR)
```

## Live Demo
- **Landing**: `http://localhost:8080/`
- **Dashboard**: `http://localhost:8080/dashboard`
- **MCP Endpoint**: `http://localhost:8080/mcp/`
- **A2A Card**: `http://localhost:8080/.well-known/agent.json`
- **x402 Manifest**: `http://localhost:8080/api/v1/feeds/x402/manifest`
- **OpenAPI Docs**: `http://localhost:8080/docs`

## How to Run
```bash
# Set up .env with Hedera credentials
cp .env.example .env
# Edit .env with your testnet credentials

# Run
python runner.py

# Or with Docker
docker compose up
```

## Tech Stack
- **Python 3.11+** with FastAPI
- **hiero-sdk-python 0.2.6** (latest)
- **hedera-agent-kit 3.4.0+**
- **MCP** (Model Context Protocol)
- **x402** (pay-triggered execution)
- **Hedera HCS** (Consensus Service)
- **HIP-991** (Custom Topic Fees)
- **HIP-1261** (Simple Fees)

## Feedback on Hedera Tools
- [hedera-agent-kit-py feedback](https://github.com/hashgraph/hedera-agent-kit-py/issues/new?template=agent_kit_feedback.yml)

## Links
- **GitHub**: https://github.com/ymiydev-prog/HashA2A
- **Twitter**: https://x.com/hasha2a
- **License**: MIT
