# HashA2A — Data Oracle for Circle Agents

## Setup

```bash
# 1. Configure your Circle Agent Wallet (if not already done)
curl -sL https://agents.circle.com/skills/setup.md | bash

# 2. Install HashA2A MCP client
npx hasha2a-mcp-client add --url https://hasha2a.com/mcp

# 3. Fund your agent wallet
circle wallet fund --amount 5 --token USDC
```

## Payment Info

- **Protocol**: x402 v2 (Circle Gateway)
- **Network**: Base (eip155:8453)
- **Asset**: USDC
- **Facilitator**: `https://gateway-api.circle.com`

## Available Services

| Service | Price (USDC) | Method | Endpoint |
|---------|-------------|--------|----------|
| Price Feed | $0.25 | `POST` | `/api/v1/feeds/prices` |
| Arbitrage Scan | $0.50 | `POST` | `/api/v1/feeds/arbitrage` |
| Arbitrage Verify | $0.10 | `GET` | `/api/v1/feeds/verify/{asset}` |
| Deep Research | $0.50 | `POST` | `/api/v1/research` |
| Prediction Market | $0.15 | `POST` | `/api/v1/requests` |
| Aggregate Data | $1.00 | `POST` | `/api/v1/requests/aggregate` |

## How to Pay

Include a `PAYMENT-SIGNATURE` header with your request.

```bash
# Example: get BTC price
curl -X POST https://hasha2a.com/api/v1/feeds/prices \
  -H "Content-Type: application/json" \
  -H "PAYMENT-SIGNATURE: $(circle x402 create --amount 0.25 --resource /api/v1/feeds/prices)" \
  -d '{"asset": "BTC/USD"}'
```

Or use the MCP client (auto-handles payments):

```bash
npx hasha2a-mcp-client add
# Then use any MCP-compatible agent to call get_price, scan_arbitrage, etc.
```

## MCP Tools

18 tools available after setup:
- **Oracle & Data**: `get_price`, `list_assets`, `get_asset_profile`, `scan_arbitrage`, `verified_feed`
- **AI & Research**: `analyze_market`, `deep_research`
- **Prediction Markets**: `list_providers`, `get_market_data`, `check_request`, `get_agent_profile`, `aggregate_market_data`
- **Hedera Kit**: `kit_setup`, `kit_account_balance`, `kit_transfer_hbar`, `kit_create_topic`, `kit_submit_message`, `kit_get_account_info`

## Support

- GitHub: https://github.com/ymiydev-prog/HashA2A
- Agent Card: `/.well-known/agent.json`
- x402 Manifest: `/.well-known/x402.json`
