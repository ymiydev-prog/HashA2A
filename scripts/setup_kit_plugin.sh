#!/usr/bin/env bash
# Setup Hedera Agent Kit plugin in isolated venv
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/../src/plugins/.kit_venv"

echo "=== HashA2A — Hedera Agent Kit Plugin Setup ==="
echo ""

if [ -f "$PLUGIN_DIR/bin/python" ]; then
    echo "Plugin venv already exists at $PLUGIN_DIR"
    read -p "Reinstall? (y/N): " REINSTALL
    if [ "$REINSTALL" != "y" ] && [ "$REINSTALL" != "Y" ]; then
        echo "Skipping."
        exit 0
    fi
    rm -rf "$PLUGIN_DIR"
fi

echo "Creating venv..."
python3 -m venv "$PLUGIN_DIR"

echo "Installing hiero-sdk-python==0.2.0..."
"$PLUGIN_DIR/bin/pip" install "hiero-sdk-python==0.2.0"

echo "Installing hedera-agent-kit..."
"$PLUGIN_DIR/bin/pip" install "hedera-agent-kit>=3.4.0"

echo ""
echo "✅ Plugin setup complete!"
echo ""
echo "Next steps:"
echo "  1. Restart HashA2A"
echo "  2. In MCP, call kit_setup() to start the plugin"
echo "  3. Use kit_account_balance(), kit_transfer_hbar(), etc."
