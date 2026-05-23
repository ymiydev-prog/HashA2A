# HashA2A — AI Prompts for Agents

Copy and paste these prompts into any AI agent (Claude, ChatGPT, Gemini, Codex, etc.)
to instantly use HashA2A's oracle intelligence, prediction markets, and research tools.

---

## Table of Contents

- [Multi-Oracle Price](#multi-oracle-price)
- [Asset Profile](#asset-profile)
- [Arbitrage Scanning](#arbitrage-scanning)
- [Prediction Markets](#prediction-markets)
- [Deep Research](#deep-research)
- [Market Analysis](#market-analysis)
- [Verified Feed](#verified-feed)
- [Provider Intelligence](#provider-intelligence)
- [Aggregate Markets](#aggregate-markets)
- [Hedera Account Balance](#hedera-account-balance)
- [HCS Topic Operations](#hcs-topic-operations)
- [HBAR Transfer](#hbar-transfer)
- [A2A Task Management](#a2a-task-management)
- [x402 Payment Flow](#x402-payment-flow)
- [JWT Authentication](#jwt-authentication)

---

## Multi-Oracle Price

```
Get the real-time BTC/USD price from all available oracles using HashA2A MCP.
Call get_price with asset="BTC/USD" and show me the median, spread, confidence,
and each oracle's individual price.
```

Variations:
- Replace `BTC/USD` with: `ETH/USD`, `HBAR/USD`, `SOL/USD`, `XAU/USD`, `AAPL/USD`, `EUR/USD`
- Add "Compare BTC/USD across all 5 oracles"
- Add "Show the price in a formatted table with confidence scores"

## Asset Profile

```
Get the complete asset profile for HBAR/USD from HashA2A. I want per-oracle prices,
24h change percentage, volume, market cap, and the spread analysis with confidence.
```

Variations:
- Replace `HBAR/USD` with any of the 36 supported assets
- Add "Show me which oracle is the fastest and which has the tightest spread"

## Arbitrage Scanning

```
Scan all 36 assets on HashA2A for cross-oracle arbitrage opportunities.
Show me the top 5 spreads ranked by opportunity, including which oracles
have the price difference and the percentage gap.
```

Variations:
- `min_spread=0.5` to filter for spreads > 0.5%
- "Check arbitrage specifically for ETH/USD across all oracles"
- "Are there any arbitrage opportunities > 1% right now?"

## Prediction Markets

```
Get prediction market data from Polymarket using HashA2A. List available
markets and show me the current probabilities for the top political events.
```

Variations:
- Replace `Polymarket` with `Kalshi`, `PredictIt`, or `Manifold`
- "Compare probabilities for the same event across Polymarket and Kalshi"
- "Get election market data from all prediction providers"

## Deep Research

```
Run a deep research query on HashA2A: "What is the current sentiment on
Ethereum ETF approvals and how are prediction markets pricing the odds?"
Use web search + news + prediction markets + AI analysis.
```

Variations:
- "Deep research on Solana DeFi protocols with highest TVL growth"
- "Research the impact of Fed rate decisions on BTC price direction"
- "What are prediction markets saying about the 2026 midterm elections?"

## Market Analysis

```
Use HashA2A's analyze_market tool with Polymarket to analyze market ID
"will-bitcoin-hit-100k-2025". Give me the AI-powered analysis including
sentiment, key drivers, and probability assessment.
```

Variations:
- Replace market ID with actual Polymarket/Kalshi market slugs
- "Analyze the AI regulation market on PredictIt"

## Verified Feed

```
Get the verified_feed for ETH/USD from HashA2A. Show me the cross-validated
median price, the IQR confidence interval, and which oracles are within range
vs outliers.
```

## Provider Intelligence

```
List all available prediction market providers on HashA2A with their
description and cost per request.
```

## Aggregate Markets

```
Aggregate prediction market data from all providers on HashA2A for
the topic "2026 elections". Show me combined probabilities and
cross-provider consensus.
```

## Hedera Account Balance

```
Use HashA2A's kit_account_balance tool to check the HBAR balance of
account 0.0.603064.
```

Variations:
- Replace account ID with any Hedera account
- "Check my Hedera wallet balance"

## HCS Topic Operations

```
Use HashA2A to create a new HCS topic with memo "my-agent-topic".
After creation, submit a message "Hello from my AI agent" to it.
```

Variations:
- "List topics or check existing topic info"
- "Submit a JSON message to topic 0.0.12345"

## HBAR Transfer

```
Use HashA2A to transfer 100 HBAR (100000000 tinybars) from the default
account to account 0.0.12345.
```

## A2A Task Management

```
Create a HashA2A A2A task via JSON-RPC 2.0: send a message/send request
to get BTC price data. Then poll for the result using tasks/get.
Save the result as an artifact.
```

Variations:
- "Stream task updates via SSE"
- "Create a context and fork it for parallel subtasks"
- "Cancel a running task"

## x402 Payment Flow

```
I want to pay for HashA2A data using USDC via x402. First, get the x402
manifest at /.well-known/x402.json to see supported rails and pricing.
Then construct a payment with PAYMENT-SIGNATURE header for a $0.25 price feed.
```

Variations:
- "Pay with HBAR via HIP-991"
- "Pay with Circle Gateway USDC"

## JWT Authentication

```
Get a JWT token from HashA2A for scope "feeds:prices" with 300 second TTL.
Then use the token to make an authenticated price request for SOL/USD.
```

---

## Quick Reference: Parameter Cheatsheet

| Tool | Required Params | Optional |
|------|----------------|----------|
| `get_price` | `asset` | — |
| `get_asset_profile` | `asset` | — |
| `scan_arbitrage` | — | `min_spread` |
| `verified_feed` | `asset` | — |
| `get_market_data` | `provider`, `market_id` | — |
| `analyze_market` | `provider`, `market_id` | — |
| `deep_research` | `query` | — |
| `check_request` | `request_id` | — |
| `aggregate_market_data` | — | `provider` |
| `kit_transfer_hbar` | `to`, `amount` | — |
| `kit_create_topic` | — | `memo` |
| `kit_submit_message` | `topic_id`, `message` | — |
| `kit_account_balance` | `account_id` | — |
| `kit_get_account_info` | `account_id` | — |

## URL Reference

- MCP Server: `http://localhost:8080/mcp`
- A2A RPC: `http://localhost:8080/api/v1/a2a/rpc`
- A2A SSE: `http://localhost:8080/api/v1/a2a/rpc/stream`
- REST API: `http://localhost:8080/api/v1/`
- Agent Card: `http://localhost:8080/.well-known/agent.json`
- x402 Manifest: `http://localhost:8080/.well-known/x402.json`
- OpenAPI Spec: `http://localhost:8080/openapi.json`
