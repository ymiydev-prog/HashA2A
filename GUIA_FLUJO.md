# Guía de Flujo: HashA2A — Agent-to-Agent Intelligence Layer

## ¿Qué es HashA2A?

HashA2A es un **oráculo de datos descentralizado** donde agentes de IA compran inteligencia procesada mediante micropagos en HBAR en la red Hedera.

**Ejemplo concreto:** Un agente de trading quiere saber "¿cuál es la probabilidad de que Rihanna lance un álbum antes de GTA VI?". HashA2A consulta Polymarket, analiza el resultado con IA, y se lo vende al agente por 0.5 HBAR.

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                   AGENTE COMPRADOR                        │
│  (otro bot / script / IA)                                │
└──────────┬──────────────┬────────────────┬───────────────┘
           │              │                │
           ▼              ▼                ▼
   ┌────────────┐ ┌────────────┐ ┌────────────────┐
   │ REST API   │ │ MCP Server │ │  HCS Message    │
   │ :8080/api  │ │ :8080/mcp  │ │  (HIP-991 fee)  │
   └──────┬─────┘ └─────┬──────┘ └───────┬────────┘
          │              │                │
          ▼              ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                    HashA2A                                │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────┐  │
│  │ Provider   │  │ AI         │  │ PaymentEngine +   │  │
│  │ Registry   │  │ Analyzer   │  │ ConsensusLogger   │  │
│  │ (4 plugins)│  │ (LangChain)│  │ (HCS + Mirror)    │  │
│  └──────┬─────┘  └─────┬──────┘  └────────┬──────────┘  │
│         │              │                   │             │
└─────────┼──────────────┼───────────────────┼─────────────┘
          │              │                   │
          ▼              ▼                   ▼
   ┌────────────┐  ┌────────────┐   ┌────────────────┐
   │ Proveedores│  │ OpenAI     │   │ Hedera Network │
   │ Reales     │  │ gpt-5-nano │   │ HCS + HIP-991  │
   └────────────┘  └────────────┘   └────────────────┘
```

---

## Flujo Paso a Paso (visión agente comprador)

### Paso 1: Descubrimiento

El comprador descubre que HashA2A existe de 3 formas:

**A) HOL Registry (HCS-10)**
```
HashA2A hace broadcast periódico al tópico 0.0.29640405:
{
  "type": "agent_broadcast",
  "agent": {
    "agent_name": "HashA2A Intelligence Oracle",
    "inbound_topic": "0.0.896XXXX",
    "outbound_topic": "0.0.896XXXX",
    "treasury_account": "0.0.7243649",
    "supported_providers": [...]
  }
}
```

**B) MCP Server**
```
http://localhost:8080/mcp/
→ GET:  JSON con info del servidor
→ POST: JSON-RPC 2.0 (initialize, tools/list, tools/call)
```

**C) REST API**
```
GET /api/v1/agent/profile    → perfil completo
GET /api/v1/agent/health     → estado del servidor
GET /api/v1/agent/discovery  → lista agentes descubiertos
```

### Paso 2: Ver qué hay disponible

El comprador consulta los providers:

```
GET /api/v1/providers
```

Respuesta:
```json
[
  {"name": "Polymarket Edge",   "cost_hbar": 0.5, "trust_score": 50},
  {"name": "Kalshi",            "cost_hbar": 0.3, "trust_score": 50},
  {"name": "PredictIt",         "cost_hbar": 0.4, "trust_score": 50},
  {"name": "Manifold Markets",  "cost_hbar": 0.3, "trust_score": 50}
]
```

O vía MCP:
```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_providers","arguments":{}}}
```

### Paso 3: Crear un request

El comprador pide datos. Ejemplo: mercados de Polymarket:

```
POST /api/v1/requests
{
  "provider_id": "polymarket",
  "params": {"limit": 3}
}
```

Respuesta:
```json
{
  "request_id": "71f352a5-17b5-4424-bcc4-61a3c18d94bb",
  "provider_name": "Polymarket Edge",
  "status": "awaiting_payment",
  "payment": {
    "amount_hbar": 0.5,
    "hip991": true,
    "inbound_topic_id": "0.0.896XXXX"
  },
  "instructions": "Envía un mensaje HCS al topic 0.0.896XXXX con {\"request_id\": \"71f...\", \"provider\": \"polymarket\", \"params\": {\"limit\": 3}}"
}
```

### Paso 4: Pagar (HIP-991)

El comprador envía un mensaje al **inbound topic** de HashA2A:

```python
from hiero_sdk_python import (
    AccountId, Client, PrivateKey,
    TopicId, TopicMessageSubmitTransaction
)

client = Client.for_testnet()
client.set_operator(
    AccountId.from_string("0.0.XXXXXXXX"),  # cuenta del comprador
    PrivateKey.from_string("...clave_privada...")
)

mensaje = {
    "request_id": "71f352a5-...",
    "provider": "polymarket",
    "params": {"limit": 3}
}

tx = TopicMessageSubmitTransaction()
tx.set_topic_id(TopicId.from_string("0.0.896XXXX"))
tx.set_message(json.dumps(mensaje))
tx.freeze_with(client)
tx.sign(private_key)
receipt = tx.execute(client)
```

**HIP-991 cobra automáticamente 0.5 HBAR** de la cuenta del comprador. No hay que hacer una transferencia separada. El cobro se ejecuta a nivel de red.

### Paso 5: Procesamiento interno

HashA2A detecta el mensaje vía sus suscripción HCS:

```
PaymentEngine._on_message()
  → _confirm_and_activate()
    → process_paid_request()
      1. provider.get_data()     ← fetch de Polymarket (API real)
      2. evaluate_quality()      ← score 0-1
      3. AIAnalyzer.analyze()    ← LangChain + gpt-5-nano
      4. consensus_logger()      ← registra en audit topic HCS
      5. _inflight[request_id]   ← almacena resultado
```

### Paso 6: Obtener resultado

El comprador hace pooling hasta que cambie el status:

```
GET /api/v1/requests/71f352a5-...
```

Respuesta cuando está listo:
```json
{
  "request_id": "71f352a5-...",
  "status": "completed",
  "quality_score": 0.8,
  "data": {
    "markets": [
      {"question": "Will Rihanna release an album before GTA VI?",
       "yes_price": 0.52, "no_price": 0.48, ...}
    ]
  },
  "analysis": "Rihanna Yes 0.52 / No 0.48 (≈52% vs 48%)...
               Slight tilt toward Yes... High activity with
               volume ~728k and liquidity ~8.5k...",
  "proof_tx_id": "0.0.7243648@1778884817.146446943",
  "audit_topic_id": "0.0.8969426"
}
```

### Paso 7: Verificar (opcional)

El comprador puede verificar la integridad:
- `proof_tx_id` → consultar en mirror node: `https://testnet.mirrornode.hedera.com/api/v1/transactions/{proof_tx_id}`
- `audit_topic_id` → suscribirse y ver el registro en HCS

---

## Diagrama de Secuencia

```
Comprador              HashA2A               Provider (API real)     Hedera
   │                      │                        │                  │
   │──GET /providers─────▶│                        │                  │
   │◀── lista ────────────│                        │                  │
   │                      │                        │                  │
   │──POST /requests─────▶│                        │                  │
   │◀── request_id + ────│                        │                  │
   │     inbound_topic    │                        │                  │
   │                      │                        │                  │
   │──HCS message────────▶│────────────────────────│─────────────────▶│
   │  (with HIP-991 fee)  │                        │                  │
   │                      │                        │                  │
   │                      │──GET /markets─────────▶│                  │
   │                      │◀── datos reales ───────│                  │
   │                      │                        │                  │
   │                      │──analyze (ChatOpenAI)──│                  │
   │                      │◀── análisis ───────────│                  │
   │                      │                        │                  │
   │                      │────────────────────────│──HCS audit──────▶│
   │                      │                        │                  │
   │──GET /requests/id───▶│                        │                  │
   │◀── datos + análisis ─│                        │                  │
   │                      │                        │                  │
```

---

## Componentes Clave

| Componente | Archivo | Función |
|------------|---------|---------|
| Provider Registry | `src/core/provider_registry.py` | Registra y descubre providers |
| Payment Engine | `src/core/payment_engine.py` | Escucha pagos HCS + Mirror Node |
| AI Analyzer | `src/core/ai_analyzer.py` | Analiza datos con LangChain + OpenAI |
| Consensus Logger | `src/core/consensus_logger.py` | Registra resultados en audit topic |
| Agent Directory | `src/core/agent_directory.py` | Tracking de agentes descubiertos |
| Agent Listener | `src/core/agent_listener.py` | Escanea HOL Registry + topics |
| MCP Server | `src/mcp_server.py` | Interfaz MCP (5 tools) |
| Dashboard | `src/api/routes/dashboard.py` | UI web con WebSocket en vivo |

## Providers

| Provider | Costo | API Real | Descripción |
|----------|-------|----------|-------------|
| Polymarket Edge | 0.5 HBAR | Polymarket Gamma | Mercados de predicción descentralizados |
| Kalshi | 0.3 HBAR | Kalshi API | Mercados regulados por CFTC (US) |
| PredictIt | 0.4 HBAR | PredictIt API | Mercados académicos (US) |
| Manifold Markets | 0.3 HBAR | Manifold API | Mercados de juego (play-money) |

## Cómo probar ahora mismo

```bash
# 1. Iniciar servidor
cd /media/yhas/_dde_data/home/yhas/Opencode/HashA2A
python runner.py

# 2. Verificar estado
curl http://localhost:8080/api/v1/agent/health
# → {"status":"healthy","hedera_connected":true,...}

# 3. Ver providers
curl http://localhost:8080/api/v1/providers

# 4. Crear request
curl -X POST http://localhost:8080/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{"provider_id":"polymarket","params":{"limit":3}}'

# 5. Abrir dashboard
# http://localhost:8080/dashboard

# 6. MCP Inspector (UI interactiva)
npx -y @modelcontextprotocol/inspector http://localhost:8080/mcp
```

> **Nota:** Todo corre en testnet con HBAR de prueba. Los datos de providers son reales. Para mainnet solo cambias `HEDERA_NETWORK=mainnet` en `.env`.
