#!/usr/bin/env node
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { homedir, platform } from "node:os";
import { resolve, dirname } from "node:path";

const MCP_URL_DEFAULT = "http://localhost:8080/mcp";

const TOOLS = [
  ["Oracle & Data", ["get_price", "list_assets", "get_asset_profile", "scan_arbitrage", "verified_feed"]],
  ["AI & Research", ["analyze_market", "deep_research"]],
  ["Prediction Markets", ["list_providers", "get_market_data", "check_request", "get_agent_profile", "aggregate_market_data"]],
  ["Hedera Agent Kit", ["kit_setup", "kit_account_balance", "kit_transfer_hbar", "kit_create_topic", "kit_submit_message", "kit_get_account_info"]],
];

function detectClients() {
  const home = homedir();
  const os = platform();
  const clients = [];

  const configs = [
    { name: "Claude Desktop", file: resolve(home, ".config/Claude/claude_desktop_config.json") },
    { name: "Claude Desktop (macOS)", file: resolve(home, "Library/Application Support/Claude/claude_desktop_config.json") },
    { name: "Cursor", file: resolve(home, ".cursor/mcp.json") },
    { name: "Cursor (macOS)", file: resolve(home, "Library/Application Support/Cursor/mcp.json") },
    { name: "Windsurf", file: resolve(home, ".codeium/windsurf/mcp_config.json") },
    { name: "Windsurf (macOS)", file: resolve(home, "Library/Application Support/Windsurf/mcp_config.json") },
    { name: "Windsurf (Linux)", file: resolve(home, ".config/Windsurf/mcp_config.json") },
  ];

  for (const c of configs) {
    try {
      const dir = dirname(c.file);
      if (existsSync(dir)) clients.push(c);
    } catch { /* skip */ }
  }
  return clients;
}

function readConfig(filePath) {
  try {
    return existsSync(filePath) ? JSON.parse(readFileSync(filePath, "utf-8")) : {};
  } catch {
    return {};
  }
}

function writeConfig(filePath, config) {
  const dir = dirname(filePath);
  mkdirSync(dir, { recursive: true });
  writeFileSync(filePath, JSON.stringify(config, null, 2) + "\n", "utf-8");
}

function install(mcpUrl, silent) {
  const clients = detectClients();
  if (clients.length === 0) {
    if (!silent) {
      console.log("\n  No MCP client detected.");
      console.log(`  Add this to your MCP client config manually:\n`);
      printManualConfig(mcpUrl);
    }
    return false;
  }

  let installed = 0;
  for (const client of clients) {
    const config = readConfig(client.file);
    if (!config.mcpServers) config.mcpServers = {};
    config.mcpServers.hashA2A = { url: mcpUrl };
    writeConfig(client.file, config);
    if (!silent) console.log(`  ✓ ${client.name}`);
    installed++;
  }

  if (!silent) {
    console.log(`\n  ✅ HashA2A MCP server added to ${installed} client(s)!\n`);
    printTools(silent);
    console.log(`  Restart your MCP client to see the tools.\n`);
  }
  return true;
}

function remove(silent) {
  const clients = detectClients();
  if (clients.length === 0) {
    if (!silent) console.log("  No MCP client detected.");
    return false;
  }

  let removed = 0;
  for (const client of clients) {
    const config = readConfig(client.file);
    if (config.mcpServers?.hashA2a) {
      delete config.mcpServers.hashA2a;
      if (Object.keys(config.mcpServers).length === 0) delete config.mcpServers;
      writeConfig(client.file, config);
      if (!silent) console.log(`  ✗ ${client.name}`);
      removed++;
    }
  }

  if (!silent && removed > 0) console.log(`\n  Removed from ${removed} client(s).\n`);
  return removed > 0;
}

function check(mcpUrl) {
  const clients = detectClients();
  if (clients.length === 0) {
    console.log("  No MCP client detected.");
    process.exit(1);
  }

  let found = 0;
  for (const client of clients) {
    const config = readConfig(client.file);
    const srv = config.mcpServers?.hashA2a;
    if (srv) {
      console.log(`  ✓ ${client.name} → ${srv.url}`);
      found++;
    } else {
      console.log(`  ○ ${client.name} → not configured`);
    }
  }
  return found;
}

function printManualConfig(mcpUrl) {
  const cfg = { mcpServers: { hashA2a: { url: mcpUrl } } };
  console.log(JSON.stringify(cfg, null, 2));
  console.log();
}

function printTools() {
  console.log("  18 MCP tools available:\n");
  for (const [group, tools] of TOOLS) {
    console.log(`    ${group}:`);
    for (const t of tools) console.log(`      • ${t}`);
    console.log();
  }
}

function printHelp() {
  console.log(`
  HashA2A MCP Client — hasha2a-mcp-client

  Usage:
    npx hasha2a-mcp-client add [--url <url>]   Install MCP server config
    npx hasha2a-mcp-client remove              Remove MCP server config
    npx hasha2a-mcp-client check [--url <url>] Check installation status
    npx hasha2a-mcp-client list-tools          Show available tools
    npx hasha2a-mcp-client                     Alias for "add"

  Options:
    --url <url>   MCP server URL (default: ${MCP_URL_DEFAULT})
    --json        JSON output (for programmatic use)
    --help        Show this help

  Examples:
    npx hasha2a-mcp-client add
    npx hasha2a-mcp-client add --url https://hasha2a.com/mcp
    npx hasha2a-mcp-client check --json
`);
}

// ── CLI ──────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const command = args[0] || "add";
const urlArg = args.find((a) => a.startsWith("--url=")) || args[args.indexOf("--url") + 1];
const mcpUrl = urlArg || MCP_URL_DEFAULT;
const isJson = args.includes("--json");
const isHelp = args.includes("--help");

if (isHelp) {
  printHelp();
  process.exit(0);
}

try {
  switch (command) {
    case "add":
    case "install": {
      const ok = install(mcpUrl, isJson);
      if (isJson) {
        const clients = detectClients();
        console.log(JSON.stringify({ installed: ok, clients: clients.map((c) => c.name), url: mcpUrl }));
      }
      process.exit(ok ? 0 : 1);
    }
    case "remove":
    case "uninstall": {
      const ok = remove(isJson);
      if (isJson) console.log(JSON.stringify({ removed: ok }));
      process.exit(ok ? 0 : 1);
    }
    case "check":
    case "status": {
      const found = check(mcpUrl);
      if (isJson) {
        const clients = detectClients();
        console.log(JSON.stringify({ configured: found, clients: clients.length }));
      }
      process.exit(found > 0 ? 0 : 1);
    }
    case "list-tools":
    case "tools":
      printTools();
      process.exit(0);
    default:
      console.error(`Unknown command: ${command}`);
      printHelp();
      process.exit(1);
  }
} catch (err) {
  console.error(`Error: ${err.message}`);
  process.exit(1);
}
