#!/usr/bin/env bash
set -euo pipefail

# HashA2A — MCP Server Installer
# One-command setup for Claude Desktop, Cursor, Windsurf, and any MCP client
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ymiydev-prog/HashA2A/main/scripts/install-mcp.sh | bash
#
# Or install manually:
#   bash scripts/install-mcp.sh

REPO="ymiydev-prog/HashA2A"
MCP_URL="${1:-http://localhost:8080/mcp}"

echo "╔══════════════════════════════════════╗"
echo "║     HashA2A — MCP Server Installer   ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "This script configures your MCP client to connect to HashA2A."
echo ""

# Detect MCP client config locations
CONFIG_DIRS=()

# Claude Desktop
if [ -d "$HOME/.config/Claude" ]; then
    CONFIG_DIRS+=("$HOME/.config/Claude")
elif [ -d "$HOME/Library/Application Support/Claude" ]; then
    CONFIG_DIRS+=("$HOME/Library/Application Support/Claude")
fi

# Cursor
if [ -d "$HOME/.cursor" ]; then
    CONFIG_DIRS+=("$HOME/.cursor")
elif [ -d "$HOME/Library/Application Support/Cursor" ]; then
    CONFIG_DIRS+=("$HOME/Library/Application Support/Cursor")
fi

# Windsurf
if [ -d "$HOME/.codeium" ]; then
    CONFIG_DIRS+=("$HOME/.codeium/windsurf")
elif [ -d "$HOME/Library/Application Support/Windsurf" ]; then
    CONFIG_DIRS+=("$HOME/Library/Application Support/Windsurf")
fi

MCP_CONFIG='{
  "mcpServers": {
    "hasha2a": {
      "url": "'"$MCP_URL"'"
    }
  }
}'

if [ ${#CONFIG_DIRS[@]} -eq 0 ]; then
    echo "No MCP client configuration directory found."
    echo ""
    echo "Add this to your MCP client config (claude_desktop_config.json, etc.):"
    echo ""
    echo "$MCP_CONFIG" | python3 -m json.tool 2>/dev/null || echo "$MCP_CONFIG"
    echo ""
    echo "Or connect directly:"
    echo "  MCP URL: $MCP_URL"
    echo "  Tools:   get_price, list_assets, scan_arbitrage, get_asset_profile,"
    echo "           deep_research, list_providers, check_request, get_agent_profile,"
    echo "           analyze_market, kit_setup, kit_account_balance, kit_transfer_hbar,"
    echo "           kit_create_topic, kit_submit_message, kit_get_account_info"
    exit 0
fi

echo "Found MCP client directories:"
for dir in "${CONFIG_DIRS[@]}"; do
    echo "  • $dir"
done
echo ""

INSTALLED=false
for dir in "${CONFIG_DIRS[@]}"; do
    if [[ "$dir" == *"Claude"* ]]; then
        CONFIG_FILE="$dir/claude_desktop_config.json"
    elif [[ "$dir" == *"cursor"* || "$dir" == *"Cursor"* ]]; then
        CONFIG_FILE="$dir/mcp.json"
    elif [[ "$dir" == *"windsurf"* || "$dir" == *"Windsurf"* ]]; then
        CONFIG_FILE="$dir/mcp_config.json"
    else
        continue
    fi

    if [ -f "$CONFIG_FILE" ]; then
        # Merge with existing config
        python3 -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
if 'mcpServers' not in config:
    config['mcpServers'] = {}
config['mcpServers']['hasha2a'] = {'url': '$MCP_URL'}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
print('✓ Updated $CONFIG_FILE')
" 2>/dev/null || {
            echo "✗ Could not update $CONFIG_FILE (trying backup method)"
            cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
            echo "$MCP_CONFIG" > "$CONFIG_FILE"
            echo "  Backup saved to ${CONFIG_FILE}.bak"
        }
        INSTALLED=true
    else
        # Create new config
        mkdir -p "$(dirname "$CONFIG_FILE")"
        echo "$MCP_CONFIG" > "$CONFIG_FILE"
        echo "✓ Created $CONFIG_FILE"
        INSTALLED=true
    fi
done

if [ "$INSTALLED" = true ]; then
    echo ""
    echo "✅ HashA2A MCP server installed!"
    echo ""
    echo "18 MCP tools available:"
    echo "  • Data:   get_price, list_assets, get_asset_profile, scan_arbitrage"
    echo "  • AI:     deep_research, analyze_market"
    echo "  • Agents: list_providers, check_request, get_agent_profile"
    echo "  • Kit:    kit_account_balance, kit_transfer_hbar, kit_create_topic,"
    echo "            kit_submit_message, kit_get_account_info, kit_setup"
    echo ""
    echo "Restart your MCP client to see the tools."
else
    echo "Could not install automatically."
    echo "Add this to your MCP client config:"
    echo "$MCP_CONFIG" | python3 -m json.tool 2>/dev/null || echo "$MCP_CONFIG"
fi
