# HashA2A — Agent memory

## Run

```bash
python runner.py                           # sets PYTHONPATH=src; port 8080
PYTHONPATH=src python -m pytest tests/ -v  # 105 tests
```

All commands must run from project root. Never run without `runner.py` or `PYTHONPATH=src` — imports break.

## Entrypoint

`runner.py` → `src/api/main.py:app` (FastAPI with `lifespan`). Uvicorn with `reload=True` — fork causes process isolation between HCS subscription thread and HTTP handlers.

## SDK (hiero-sdk-python v0.2.6)

Non-obvious API quirks discovered by fixing repeated runtime errors:

| Expectation | Reality |
|---|---|
| `execute_async()` | `execute()` is **sync**. Wrap in `asyncio.to_thread(tx.execute, client)`. |
| `get_receipt_async()` | `execute()` **already returns** `TransactionReceipt` directly. No separate receipt fetch. |
| `set_topic_memo()` | Named `set_memo()`. |
| `set_amount_in_tinybars()` | Deprecated. Use `set_hbar_amount(Hbar.from_tinybars(n))`. |
| `TopicMessageQuery.set_topic_id(topic_id)` | Expects **string**, not `TopicId` object. Use `str(topic_id)`. |
| Default `tx.transaction_fee` | Causes `INSUFFICIENT_TX_FEE` (status 9) for topic creation. Must set explicitly — 30 HBAR for basic topics, 50 HBAR for HIP-991 topics. |
| `PriviateKey.from_string()` | Supports both DER (48 bytes) and raw (32 bytes Ed25519) hex. |
| Mainnet TLS cert hash | SDK 0.2.6 hardcodes stale cert hash → `ValueError`. Fix: monkey-patch `_Node._validate_tls_certificate_with_trust_manager = lambda self: None` in `hedera_manager.py`. |

## Config

`src/core/config.py` reads `.env` via Pydantic. `.env` is in `.gitignore` — secrets never committed.

- `HEDERA_OPERATOR_ID` / `HEDERA_OPERATOR_KEY` — required for Hedera ops
- `TREASURY_ACCOUNT` / `TREASURY_PRIVATE_KEY` — receives HIP-991 fees
- `OPENAI_API_KEY` — optional, enables AI analysis
- `LANGCHAIN_MODEL` — model name (e.g. `gpt-5-nano`, `gpt-4o-mini`)

Default settings in `Settings` class work with empty `.env` (graceful degradation, `hedera_connected: false`).

## Architecture

- **lifespan** initializes all components (HederaManager, PaymentEngine, AgentRegistry, ProviderRegistry, etc.)
- **PaymentEngine** subscribes to HCS topic in a daemon thread + falls back to Mirror Node REST polling every `payment_ttl_seconds`
- **MCP** uses `StreamableHTTPSessionManager` — session lifecycle wrapped in `async with mcp._session_manager.run():` inside lifespan
- **MCP endpoint** is mounted at `/mcp/` via custom ASGI (`mcp_asgi` function in `main.py`). GET returns JSON info, POST delegates to `app.state.mcp_app`.

## Providers

5 real-API providers, all in `src/providers/`:
- `polymarket` (0.5 HBAR) — Polymarket Gamma API
- `kalshi` (0.3 HBAR) — Kalshi external-api
- `predictit` (0.4 HBAR) — PredictIt marketdata
- `manifold` (0.3 HBAR) — Manifold v0 API
- `hyperliquid` (0.3 HBAR) — Hyperliquid HIP-4 Info API

New providers extend `BettingDataProvider` (`providers/base_betting.py`), register in `lifespan` in `main.py`.

## Data flow

1. Agent POSTs `/api/v1/requests` → gets `request_id` + `inbound_topic_id`
2. Agent sends HCS message to that topic (HIP-991 auto-collects fee)
3. PaymentEngine detects message → calls `process_paid_request()`
4. `process_paid_request()`: fetch data → evaluate quality → AI analysis (if OpenAI key) → store result
5. Agent polls `GET /api/v1/requests/{id}` for result

## AI Analysis

`src/core/ai_analyzer.py` — `AIAnalyzer.analyze(provider_id, data)` → text analysis. Uses `ChatOpenAI` (sync `.invoke()`). Provider-specific context prompts. Silent fallback (returns None) if no `OPENAI_API_KEY`.

Import note: LangChain ≥1.2 moved message classes to `langchain_core.messages` (not `langchain.schema`).

## MCP

19 tools: `get_price`, `list_assets`, `get_asset_profile`, `scan_arbitrage`, `verified_feed`, `list_providers`, `get_market_data`, `check_request`, `get_agent_profile`, `analyze_market`, `deep_research`, `aggregate_market_data`, `kit_setup`, `kit_account_balance`, `kit_transfer_hbar`, `kit_create_topic`, `kit_submit_message`, `kit_topic_messages`, `kit_get_account_info`.

Streamable HTTP protocol requires `Accept: application/json, text/event-stream` header. After `initialize`, subsequent requests need `Mcp-Session-Id` header. Debug with:

```bash
npx -y @modelcontextprotocol/inspector http://localhost:8080/mcp
```

## README

READme está actualizado y refleja el estado real del proyecto (mainnet, 19 tools, 36 assets, 5 oracles, pricing dinámico, calidad, subastas, staking).

## Package npm

`packages/mcp-client/` — CLI tool `hasha2a-mcp-client` (publicado en npm registry).

```bash
npx hasha2a-mcp-client add
```

## Universal SKILL

`skills/hasha2a/SKILL.md` — formato estándar `skills.sh` que enseña a cualquier agente (Claude Code, Gemini CLI, Codex CLI) cómo usar HashA2A.

```bash
npx skills add ymiydev-prog/HashA2A --skill hasha2a -g -y
```

## AI Prompts

`docs/ai-prompts.md` — 15 prompts copia-pega para todos los 19 MCP tools, API REST, payment flows y operaciones Hedera.

## Circle Agent Wallet Integration

`X402CircleHandler` en `src/core/x402.py` — extiende `X402Handler` con Circle Gateway como facilitator.

- **Manifiesto**: `/api/v1/feeds/x402/manifest` incluye `rails.circle_gateway`
- **Skill para agentes**: `/.well-known/circle/skill.md`
- **x402.json actualizado**: incluye `circle_gateway` block

Los agentes Circle se autoconfiguran con:
```bash
curl -sL https://agents.circle.com/skills/setup.md | bash
npx hasha2a-mcp-client add
```

## Checklist — Discoverability (pendiente)

- [x] **Publicar npm package**: `hasha2a-mcp-client@0.1.0` en npm registry
- [x] **Plugin n8n**: `packages/n8n-nodes-hasha2a/` — 6 operaciones, compila y testea OK
- [x] **Publicar n8n node**: `hasha2a-n8n-nodes@0.1.0` en npm registry
- [x] **Circle Gateway**: `X402CircleHandler` + skill + manifest
- [ ] **Listar HashA2A en Circle Marketplace**: ir a `agents.circle.com/for-sellers` → registrar como seller
- [ ] **Registrar en smithery.ai**: ir a https://smithery.ai/new → pegar URL pública del MCP
- [ ] **Registrar en mcp.so**: ir a https://mcp.so → submit server info
- [x] **OpenAPI spec**: `/openapi.json` generado automáticamente por FastAPI (57 paths, 15 schemas), copia estática en `static/openapi.json`
- [ ] **Subir a APIS.guru**: hacer PR en https://github.com/APIs-guru/openapi-directory (requiere URL pública)
- [x] **Artículo Dev.to/Medium**: draft en `docs/devto-article.md`
- [ ] **Publicar artículo**: copiar/pegar `docs/devto-article.md` en Dev.to o Medium
- [x] **Universal SKILL**: `skills/hasha2a/SKILL.md` + `skills/hasha2a/references/core.md` — `npx skills add ymiydev-prog/HashA2A --skill hasha2a`
- [x] **AI Prompts**: `docs/ai-prompts.md` — 15 prompts para agentes
- [ ] **Deploy VPS**: Hostinger + Traefik + Docker stack con URL pública
