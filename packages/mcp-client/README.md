# hasha2a-mcp-client

One-command MCP client setup for **HashA2A** — the Agent-to-Agent Intelligence Layer on Hedera.

## Usage

```bash
# Auto-detect and configure Claude Desktop / Cursor / Windsurf
npx hasha2a-mcp-client add

# Or point to a remote server
npx hasha2a-mcp-client add --url https://hasha2a.com/mcp

# Check installation status
npx hasha2a-mcp-client check

# Remove the config
npx hasha2a-mcp-client remove

# List available tools
npx hasha2a-mcp-client list-tools
```

## Commands

| Command | Description |
|---------|-------------|
| `add` / `install` | Add HashA2A to MCP client config |
| `remove` / `uninstall` | Remove from config |
| `check` / `status` | Check if configured |
| `list-tools` / `tools` | Show 18 available tools |

## Options

| Flag | Description |
|------|-------------|
| `--url <url>` | MCP server URL (default: `http://localhost:8080/mcp`) |
| `--json` | JSON output for programmatic use |
| `--help` | Show help |

## Supported Clients

- Claude Desktop
- Cursor
- Windsurf

## 19 MCP Tools

**Oracle & Data**: `get_price`, `list_assets`, `get_asset_profile`, `scan_arbitrage`, `verified_feed`
**AI & Research**: `analyze_market`, `deep_research`
**Prediction Markets**: `list_providers`, `get_market_data`, `check_request`, `get_agent_profile`, `aggregate_market_data`
**Hedera Agent Kit**: `kit_setup`, `kit_account_balance`, `kit_transfer_hbar`, `kit_create_topic`, `kit_submit_message`, `kit_topic_messages`, `kit_get_account_info`

## Publish

```bash
npm publish --access public
```
