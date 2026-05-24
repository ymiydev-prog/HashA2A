# @hasha2a/n8n-nodes-hasha2a

n8n community node for **HashA2A** — multi-oracle prices, arbitrage, prediction markets, and deep research on Hedera.

## Install

```bash
npm install @hasha2a/n8n-nodes-hasha2a
```

Then restart n8n and find **HashA2A** in the node panel.

## Operations

| Operation | Description |
|-----------|-------------|
| **Get Price** | Multi-oracle price for BTC, ETH, SOL, HBAR, and 36 assets |
| **List Assets** | List all supported assets with metadata |
| **Scan Arbitrage** | Cross-oracle arbitrage opportunities |
| **Deep Research** | Web + news + AI analysis |
| **Get Market Data** | Prediction markets (Polymarket, Kalshi, etc.) |
| **Aggregate Data** | Multi-provider intelligence |

## Configuration

| Field | Description |
|-------|-------------|
| **Server URL** | HashA2A server URL (default: `http://localhost:8080`) |
| **API Key** | Optional JWT token |

## Publish

```bash
npm publish --access public
```
