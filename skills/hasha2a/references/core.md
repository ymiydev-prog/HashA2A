# HashA2A Core Reference

## Server

| Detail | Value |
|--------|-------|
| Default URL | `http://localhost:8080` |
| Public URL | `https://hasha2a.com` (when deployed) |
| Network | Hedera mainnet |
| Operator | `0.0.603064` |

## MCP Tools (19)

### Oracle & Data

| Tool | Params | Returns |
|------|--------|---------|
| `get_price` | `asset` (str, e.g. `"BTC/USD"`) | Multi-oracle price object with all sources, median, spread, confidence |
| `list_assets` | None | All 36 assets grouped by category (crypto, equities, commodities, forex) |
| `get_asset_profile` | `asset` (str) | Full profile — per-source prices, 24h change, volume, market cap, spread, confidence |
| `scan_arbitrage` | `min_spread` (optional float) | Cross-oracle spreads across all assets, ranked by opportunity |
| `verified_feed` | `asset` (str) | Cross-validated feed with median, IQR confidence interval, all source prices |

### Prediction Markets & Research

| Tool | Params | Returns |
|------|--------|---------|
| `list_providers` | None | Polymarket, Kalshi, PredictIt, Manifold — description + cost |
| `get_market_data` | `provider` (str), `market_id` (str) | Market data from chosen provider |
| `check_request` | `request_id` (str) | Poll result for previous request |
| `get_agent_profile` | `agent_id` (optional str) | Agent identity and reputation |
| `aggregate_market_data` | `provider` (optional str) | Multi-provider intelligence |
| `analyze_market` | `provider` (str), `market_id` (str) | AI analysis of market data (requires OpenAI key) |
| `deep_research` | `query` (str) | Full web+news+social+prediction markets+AI research |

### Enterprise Plugin (Hedera Agent Kit)

| Tool | Params | Returns |
|------|--------|---------|
| `kit_setup` | None | Setup isolated hedera-agent-kit environment |
| `kit_account_balance` | `account_id` (str) | HBAR balance |
| `kit_transfer_hbar` | `to` (str), `amount` (int, tinybars) | Transfer HBAR |
| `kit_create_topic` | `memo` (optional str) | Create HCS topic |
| `kit_submit_message` | `topic_id` (str), `message` (str) | Submit HCS message |
| `kit_topic_messages` | `topic_id` (str), `limit` (int) | Get messages from HCS topic (Mirror Node) |
| `kit_get_account_info` | `account_id` (str) | Account details |

## REST API

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

### Prediction Markets

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/requests` | Buy prediction data |
| POST | `/api/v1/requests/aggregate` | Multi-provider aggregation |
| POST | `/api/v1/research` | Deep research |

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/token` | Request ephemeral JWT |
| POST | `/api/v1/auth/verify` | Verify Bearer token |
| POST | `/api/v1/auth/mandates` | Create AP2 mandate |
| POST | `/api/v1/auth/mandates/{id}/authorize` | Authorize spending |

### Agent Discovery

| Path | Description |
|------|-------------|
| `/.well-known/agent.json` | A2A Agent Card |
| `/.well-known/x402.json` | x402 payment manifest |
| `/llms.txt` | LLM-readable docs |
| `/mcp/` | MCP server info (GET) + Streamable HTTP (POST) |

## Pricing

| Product | USDC | HBAR (live) |
|---------|------|-------------|
| Price Feed (single asset) | $0.25 | ≈ 2.76 HBAR |
| Arbitrage Scan (all 36 assets) | $0.50 | ≈ 5.52 HBAR |
| Arbitrage Verify (single pair) | $0.10 | ≈ 1.10 HBAR |
| Deep Research | $0.50 | ≈ 5.52 HBAR |
| Prediction Market (per provider) | $0.15 | ≈ 1.66 HBAR |
| Aggregate Intelligence (all sources) | $1.00 | ≈ 11.05 HBAR |

All use **HIP-1261 Simple Fees** — `transaction_fee` is a MAX cap (0.05 HBAR basic, 0.1 HBAR for HIP-991).

## Assets — 36 Across 5 Sources

| Source | Assets | Type |
|--------|--------|------|
| **Pyth Hermes** | BTC, ETH, SOL, XAU, XAG, USD/JPY + 7 equities | First-party institutions |
| **CoinGecko** | 17 crypto assets | CEX/DEX aggregation |
| **DeFiLlama** | BTC, ETH, SOL (Chainlink via DeFiLlama) | Chainlink data feed |
| **Binance** | BTC, ETH, SOL, BNB, XRP, ADA + more | Centralized exchange |
| **ForexAPI** | EUR/USD, GBP/USD, AUD/USD, CAD/USD, CHF/USD, CNH/USD | Open exchange rates |

### Crypto (21)
BTC/USD, ETH/USD, SOL/USD, HBAR/USD, BNB/USD, XRP/USD, ADA/USD, DOGE/USD, AVAX/USD, DOT/USD, LINK/USD, UNI/USD, MATIC/USD, LTC/USD, AAVE/USD, ATOM/USD, ARB/USD, APT/USD, OP/USD, SUI/USD, PEPE/USD

### Equities (7)
AAPL/USD, MSFT/USD, NVDA/USD, GOOGL/USD, AMZN/USD, TSLA/USD, META/USD

### Commodities (2)
XAU/USD (Gold), XAG/USD (Silver)

### Forex (6)
EUR/USD, GBP/USD, AUD/USD, CAD/USD, CHF/USD, CNH/USD

## Payment Rails

### 1. HBAR (HIP-991)
- Agent sends HCS message to topic with fee
- Auto-collects via HIP-991 custom fees
- transaction_fee: 0.1 HBAR max

### 2. USDC x402 (Base + AP2)
- HTTP 402 Payment Required flow
- PAID-RESOURCE + PAYMENT-SIGNATURE headers
- 6-rule verification: layout, amount, fee payer safety, signature, nonce, asset

### 3. Circle Gateway
- Gasless USDC via Circle Agent Wallet
- Facilitator: `https://gateway-api.circle.com`
- Network: Base (eip155:8453)

## Authentication

- **JWT tokens**: POST `/api/v1/auth/token` with `scope` (60s–3600s TTL)
- **AP2 mandates**: Create + authorize spending mandates
- **x402**: Header-based payment verification (no pre-auth)

## A2A Protocol

- Agent Card: `/.well-known/agent.json` (5 skills, JSON Schema definitions)
- JSON-RPC 2.0 methods: `message/send`, `message/stream`, `tasks/get`, `tasks/list`, `tasks/cancel`
- SSE streaming for real-time updates
- Context passing with `contextId`, `ContextSummary`, `fork_context()`
- Task lifecycle: `submitted → working → input-required → completed/failed/canceled/rejected`
