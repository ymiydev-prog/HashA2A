<!-- ============================================================ -->
<!-- ESPAÑOL                                                      -->
<!-- ============================================================ -->

# HashA2A — The Agent-to-Agent Intelligence Layer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Hedera-HCS%20%7C%20HTS%20%7C%20HIP--991-green" alt="Hedera">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">
</p>

**HashA2A** es un oráculo de datos modular donde agentes de IA compran información procesada mediante micropagos en HBAR sobre Hedera. El sistema es agnóstico al tipo de dato: utiliza un sistema de plugins `DataProvider` que permite conectar cualquier fuente de datos externa y entregarla con valor agregado de inteligencia artificial.

> **Filosofía:** No vendemos datos crudos. Vendemos inteligencia procesada con prueba de consenso en HCS.

---

## Tabla de Contenidos

- [¿Qué problema resuelve?](#qué-problema-resuelve)
- [Arquitectura](#arquitectura)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Sistema de Plugins](#sistema-de-plugins)
- [Auto-promoción del Agente](#auto-promoción-del-agente)
- [Modelo de Reputación](#modelo-de-reputación)
- [Roadmap](#roadmap)

---

## ¿Qué problema resuelve?

| Problema | Solución HashA2A |
|----------|-----------------|
| Cada API requiere registro, API keys y facturación | Pago único en HBAR, sin registro |
| No hay forma de verificar la procedencia del dato | Cada respuesta se registra en HCS con hash SHA-256 |
| Los datos crudos requieren procesamiento adicional | Los DataProviders entregan datos + análisis con IA |
| No hay estándar entre fuentes de datos | `BaseDataProvider` unifica la interfaz |
| Los agentes no pueden descubrirse entre sí | Registro HCS-10 en HOL + broadcasts periódicos |

---

## Arquitectura

```
                        ┌──────────────────────────────┐
                        │     HOL Registry (HCS-10)     │
                        │  HashA2A — agente descubrible │
                        └──────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
         Agent A              Agent B              Agent C
        (LangChain)          (CrewAI)            (ElizaOS)
              │                    │                    │
              └─────────┬──────────┴──────────┬─────────┘
                        │   Pago en HBAR       │
                        │   + memo único       │
                        ▼                      ▼
              ┌──────────────────────────────────────┐
              │           HashA2A Core               │
              │  ┌────────────┐  ┌────────────────┐  │
              │  │ Payment    │  │ Provider       │  │
              │  │ Engine     │──│ Registry       │  │
              │  └────────────┘  └───────┬────────┘  │
              │                          ▼           │
              │  ┌──────────────────────────────┐    │
              │  │     BettingDataProvider       │    │
              │  │  ┌──────────┐ ┌──────────┐   │    │
              │  │  │Polymarket│ │  Kalshi  │...│    │
              │  │  └──────────┘ └──────────┘   │    │
              │  └──────────────────────────────┘    │
              │  ┌──────────────────────────────┐    │
              │  │    ConsensusLogger (HCS)      │    │
              │  └──────────────────────────────┘    │
              └──────────────────────────────────────┘
```

### Flujo de operación

```
Agente Cliente              HashA2A Core                    Hedera Network
     │                           │                              │
     ├─ POST /api/v1/requests ───>                              │
     │  {provider: "polymarket"}                                │
     │                           │                              │
     │<── Payment instructions ──│                              │
     │   {0.5 HBAR, cuenta, memo}                               │
     │                           │                              │
     ├─ Envía HBAR con memo ──────────────────────────────────>│
     │                           │                              │
     │                           │<── Poll Mirror Node ─────────│
     │                           │    (memo coincide)           │
     │                           │                              │
     │                           ├── Provider.get_data()        │
     │                           │   (fetch + IA analysis)      │
     │                           │                              │
     │                           ├── HCS: audit record ────────>│
     │                           │   (hash SHA-256 inmutables)  │
     │                           │                              │
     │<── GET /api/v1/requests/id ──│                           │
     │   {data, analysis, proof}  │                              │
```

### Componentes core

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| **BaseDataProvider** | `core/base_provider.py` | Clase base abstracta para todo proveedor de datos |
| **HederaManager** | `core/hedera_manager.py` | Topics HCS, mensajes, hashes, memos de pago |
| **PaymentEngine** | `core/payment_engine.py` | Polling de Mirror Node, matching de pagos |
| **ConsensusLogger** | `core/consensus_logger.py` | Registro de auditoría inmutable en HCS |
| **AgentRegistry** | `core/agent_registry.py` | Auto-promoción HCS-10 + broadcasts periódicos |
| **ProviderRegistry** | `core/provider_registry.py` | Registro y auto-descubrimiento de plugins |
| **BettingDataProvider** | `providers/betting/base.py` | Base especializada para sistemas de apuestas |
| **PolymarketBettingProvider** | `providers/betting/polymarket.py` | Implementación concreta para Polymarket |

---

## Quick Start

### Prerrequisitos

- Python 3.11+
- Cuenta en [Hedera Testnet](https://portal.hedera.com/)
- Una cuenta treasury con HBAR de test

### Instalación

```bash
git clone https://github.com/ymiydev-prog/HashA2A.git
cd HashA2A
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales de Hedera Testnet
```

### Ejecutar

```bash
python runner.py
# Servidor en http://localhost:8080
```

### Probar

```bash
# Listar proveedores
curl http://localhost:8080/api/v1/providers

# Perfil del agente
curl http://localhost:8080/api/v1/agent/profile

# Solicitar datos
curl -X POST http://localhost:8080/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{"provider_id": "polymarket", "params": {"query": "Bitcoin", "limit": 3}}'

# Ver resultado
curl http://localhost:8080/api/v1/requests/{request_id}
```

---

## API Endpoints

### Proveedores

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/providers` | Lista todos los proveedores con precios y reputación |
| `GET` | `/api/v1/providers/{id}` | Detalle de un proveedor específico |

### Solicitudes de datos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/requests` | Solicitar datos. Devuelve instrucciones de pago |
| `GET` | `/api/v1/requests/{id}` | Consultar resultado. Poll hasta `status = "completed"` |

### Auto-promoción del agente

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/agent/profile` | Perfil completo del agente |
| `POST` | `/api/v1/agent/broadcast` | Forzar broadcast de presencia al Outbound Topic |
| `POST` | `/api/v1/agent/register-hol` | Registrar en el HOL Registry global (HCS-10) |
| `GET` | `/api/v1/agent/topics` | Ver IDs de los topics HCS activos |

### Ejemplo completo en Python

```python
import httpx, time
BASE = "http://localhost:8080/api/v1"

resp = httpx.post(f"{BASE}/requests", json={
    "provider_id": "polymarket",
    "params": {"query": "Ethereum", "limit": 5, "include_analysis": True}
})
data = resp.json()
request_id = data["request_id"]
print(f"Envía {data['payment']['amount_hbar']} HBAR con memo '{data['payment']['memo']}'")

for _ in range(30):
    resp = httpx.get(f"{BASE}/requests/{request_id}")
    result = resp.json()
    if result.get("status") == "completed":
        print("Datos:", result["data"])
        print("Análisis:", result["analysis"])
        print("Prueba HCS:", result["proof_tx_id"])
        break
    time.sleep(2)
```

---

## Sistema de Plugins

Jerarquía de proveedores:

```
BaseDataProvider (core/base_provider.py)
  ├── BettingDataProvider (providers/betting/base.py)
  │   ├── PolymarketBettingProvider
  │   ├── KalshiBettingProvider    [futuro]
  │   └── ...
  ├── WeatherDataProvider          [futuro]
  ├── SportsDataProvider           [futuro]
  └── FinanceDataProvider          [futuro]
```

### Crear un nuevo DataProvider

```python
from typing import Any
from core.base_provider import BaseDataProvider
from models.schemas import DataResponse, RequestStatus

class WeatherDataProvider(BaseDataProvider):
    provider_id = "weather"
    name = "Weather Service"
    description = "Datos meteorológicos en tiempo real con pronósticos IA"
    cost_hbar = 0.1

    async def get_data(self, params: dict[str, Any]) -> DataResponse:
        return DataResponse(
            request_id=params.get("request_id", ""),
            provider_id=self.provider_id,
            status=RequestStatus.COMPLETED,
            data={"temperature": 22.5, "humidity": 65},
            analysis="Cielo despejado, temperaturas suaves.",
            provider_trust_score=self.reputation.trust_score,
        )
```

Registrar en `api/main.py`:

```python
from providers.weather import WeatherDataProvider
provider_registry.register(WeatherDataProvider())
```

### Añadir un nuevo sistema de apuestas

```python
# providers/betting/kalshi.py
from providers.betting.base import BettingDataProvider
from providers.betting.schemas import BettingMarket, BettingQuery

class KalshiBettingProvider(BettingDataProvider):
    provider_id = "kalshi"
    name = "Kalshi"
    description = "Mercados de predicción regulados en EE.UU."
    cost_hbar = 0.3

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        ...

    async def get_market(self, market_id: str) -> BettingMarket | None:
        ...
```

Registrar y listo. `BettingDataProvider` te da gratis: análisis de odds, cálculo de confianza, riesgos, respuesta estandarizada e integración con pagos + HCS.

---

## Auto-promoción del Agente

HashA2A se promociona automáticamente en el ecosistema Hedera.

### 1. Registro HOL (HCS-10)

```bash
curl -X POST http://localhost:8080/api/v1/agent/register-hol
```

Publica un mensaje de registro en el topic global de HOL siguiendo el estándar **HCS-10 OpenConvAI**:

```json
{
  "type": "hcs10-registration",
  "protocol": "HCS-10",
  "agent_name": "HashA2A Intelligence Oracle",
  "tags": ["data-oracle", "hedera", "prediction-markets"],
  "inbound_topic": "0.0.xxxxx",
  "outbound_topic": "0.0.xxxxx",
  "treasury_account": "0.0.xxxxx",
  "fees": { "token": "HBAR", "model": "per_request" }
}
```

### 2. Broadcasts periódicos

Cada `AGENT_PROMOTIONAL_INTERVAL` segundos (default: 1 hora), HashA2A publica su perfil actualizado en su Outbound Topic: proveedores disponibles, precios, trust scores, solicitudes servidas.

### 3. Perfil público

```bash
curl http://localhost:8080/api/v1/agent/profile
```

Devuelve un `AgentProfile` completo con toda la información que otros agentes necesitan.

---

## Modelo de Reputación

| Factor | Peso | Descripción |
|--------|------|-------------|
| Accuracy | 35% | Precisión histórica de los datos |
| Velocidad | 20% | Latencia promedio de respuesta |
| Uptime | 15% | Disponibilidad del proveedor |
| Disputas | 10% | Ratio de disputas sobre total |
| Staking | 20% | HBAR en garantía |

```python
trust_score = (
    0.35 * accuracy +
    0.20 * (100 - min(latency_ms / 100, 100)) +
    0.15 * uptime +
    0.10 * (100 - dispute_rate * 100) +
    0.20 * min(staked_hbar / 10000 * 100, 100)
)
```

---

## Roadmap

- [x] Core base: BaseDataProvider, HederaManager, PaymentEngine, ConsensusLogger
- [x] Plugin system: ProviderRegistry con auto-descubrimiento
- [x] Nicho betting: BettingDataProvider + PolymarketBettingProvider
- [x] Auto-promoción: HCS-10 / HOL registry + broadcasts periódicos
- [ ] HIP-991: Migrar de polling Mirror Node a Custom Fees en topics
- [ ] Kalshi provider: Segundo plugin de betting
- [ ] Evaluación de calidad: No cobrar si el dato no pasa threshold
- [ ] Subastas inversas: Múltiples proveedores compiten por una solicitud
- [ ] Staking real: Proveedores depositan HBAR como garantía
- [ ] MCP Server: Exponer HashA2A como servidor MCP
- [ ] x402 protocol: Soporte para pagos HTTP 402 (USDC)
- [ ] Dashboard: UI en tiempo real con estado del agente

---

## Tech Stack

| Tecnología | Uso |
|-----------|-----|
| **Python 3.11+** | Lenguaje base |
| **FastAPI** | API REST |
| **Hedera SDK** | HCS topics, mensajes, pagos |
| **Pydantic** | Modelos y validación |
| **httpx** | Cliente HTTP async |
| **LangChain** | (futuro) Procesamiento con IA |

---

## Licencia

MIT

---

<br>

<!-- ============================================================ -->
<!-- ENGLISH                                                     -->
<!-- ============================================================ -->

# HashA2A — The Agent-to-Agent Intelligence Layer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Hedera-HCS%20%7C%20HTS%20%7C%20HIP--991-green" alt="Hedera">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">
</p>

**HashA2A** is a modular data oracle where AI agents purchase processed intelligence through HBAR micropayments on Hedera. The system is data-type agnostic — it uses a `DataProvider` plugin system that can connect to any external data source and deliver it augmented with AI-driven analysis.

> **Philosophy:** We don't sell raw data. We sell processed intelligence with HCS consensus proof.

---

## Table of Contents

- [What problem does it solve?](#what-problem-does-it-solve)
- [Architecture](#architecture)
- [Quick Start](#quick-start-1)
- [API Endpoints](#api-endpoints-1)
- [Plugin System](#plugin-system)
- [Agent Self-Promotion](#agent-self-promotion)
- [Reputation Model](#reputation-model)
- [Roadmap](#roadmap-1)

---

## What problem does it solve?

| Problem | HashA2A Solution |
|----------|-----------------|
| Every API requires registration, API keys, and billing | Pay-per-query in HBAR, no registration |
| No way to verify data provenance | Every response recorded on HCS with SHA-256 hash |
| Raw data requires post-processing | DataProviders deliver data + AI analysis |
| No standardization across data sources | `BaseDataProvider` unifies the interface |
| Agents can't discover each other | HCS-10 HOL registration + periodic broadcasts |

---

## Architecture

```
                        ┌──────────────────────────────┐
                        │     HOL Registry (HCS-10)     │
                        │  HashA2A — discoverable agent │
                        └──────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
         Agent A              Agent B              Agent C
        (LangChain)          (CrewAI)            (ElizaOS)
              │                    │                    │
              └─────────┬──────────┴──────────┬─────────┘
                        │   HBAR payment       │
                        │   + unique memo      │
                        ▼                      ▼
              ┌──────────────────────────────────────┐
              │           HashA2A Core               │
              │  ┌────────────┐  ┌────────────────┐  │
              │  │ Payment    │  │ Provider       │  │
              │  │ Engine     │──│ Registry       │  │
              │  └────────────┘  └───────┬────────┘  │
              │                          ▼           │
              │  ┌──────────────────────────────┐    │
              │  │     BettingDataProvider       │    │
              │  │  ┌──────────┐ ┌──────────┐   │    │
              │  │  │Polymarket│ │  Kalshi  │...│    │
              │  │  └──────────┘ └──────────┘   │    │
              │  └──────────────────────────────┘    │
              │  ┌──────────────────────────────┐    │
              │  │    ConsensusLogger (HCS)      │    │
              │  └──────────────────────────────┘    │
              └──────────────────────────────────────┘
```

### Operation flow

```
Client Agent                HashA2A Core                    Hedera Network
     │                           │                              │
     ├─ POST /api/v1/requests ───>                              │
     │  {provider: "polymarket"}                                │
     │                           │                              │
     │<── Payment instructions ──│                              │
     │   {0.5 HBAR, account, memo}                              │
     │                           │                              │
     ├─ Sends HBAR with memo ──────────────────────────────────>│
     │                           │                              │
     │                           │<── Poll Mirror Node ─────────│
     │                           │    (memo matches)            │
     │                           │                              │
     │                           ├── Provider.get_data()        │
     │                           │   (fetch + AI analysis)      │
     │                           │                              │
     │                           ├── HCS: audit record ────────>│
     │                           │   (immutable SHA-256 hashes) │
     │                           │                              │
     │<── GET /api/v1/requests/id ──│                           │
     │   {data, analysis, proof}  │                              │
```

### Core components

| Module | File | Responsibility |
|--------|------|----------------|
| **BaseDataProvider** | `core/base_provider.py` | Abstract base class for all data providers |
| **HederaManager** | `core/hedera_manager.py` | HCS topics, messages, hashes, payment memos |
| **PaymentEngine** | `core/payment_engine.py` | Mirror Node polling, payment matching |
| **ConsensusLogger** | `core/consensus_logger.py` | Immutable audit trail on HCS |
| **AgentRegistry** | `core/agent_registry.py` | HCS-10 self-promotion + periodic broadcasts |
| **ProviderRegistry** | `core/provider_registry.py` | Plugin registration and auto-discovery |
| **BettingDataProvider** | `providers/betting/base.py` | Specialized base for betting/prediction systems |
| **PolymarketBettingProvider** | `providers/betting/polymarket.py` | Concrete implementation for Polymarket |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Hedera Testnet](https://portal.hedera.com/) account
- A treasury account with test HBAR

### Installation

```bash
git clone https://github.com/ymiydev-prog/HashA2A.git
cd HashA2A
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Hedera Testnet credentials
```

### Run

```bash
python runner.py
# Server at http://localhost:8080
```

### Test

```bash
# List providers
curl http://localhost:8080/api/v1/providers

# Agent profile
curl http://localhost:8080/api/v1/agent/profile

# Request data
curl -X POST http://localhost:8080/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{"provider_id": "polymarket", "params": {"query": "Bitcoin", "limit": 3}}'

# Check result
curl http://localhost:8080/api/v1/requests/{request_id}
```

---

## API Endpoints

### Providers

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/providers` | List all providers with pricing and reputation |
| `GET` | `/api/v1/providers/{id}` | Detail of a specific provider |

### Data requests

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/requests` | Request data. Returns payment instructions |
| `GET` | `/api/v1/requests/{id}` | Check result. Poll until `status = "completed"` |

### Agent self-promotion

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/agent/profile` | Full agent profile |
| `POST` | `/api/v1/agent/broadcast` | Force broadcast to Outbound Topic |
| `POST` | `/api/v1/agent/register-hol` | Register in HOL global registry (HCS-10) |
| `GET` | `/api/v1/agent/topics` | View active HCS topic IDs |

### Full Python example

```python
import httpx, time
BASE = "http://localhost:8080/api/v1"

resp = httpx.post(f"{BASE}/requests", json={
    "provider_id": "polymarket",
    "params": {"query": "Ethereum", "limit": 5, "include_analysis": True}
})
data = resp.json()
request_id = data["request_id"]
print(f"Send {data['payment']['amount_hbar']} HBAR with memo '{data['payment']['memo']}'")

for _ in range(30):
    resp = httpx.get(f"{BASE}/requests/{request_id}")
    result = resp.json()
    if result.get("status") == "completed":
        print("Data:", result["data"])
        print("Analysis:", result["analysis"])
        print("HCS Proof:", result["proof_tx_id"])
        break
    time.sleep(2)
```

---

## Plugin System

Provider hierarchy:

```
BaseDataProvider (core/base_provider.py)
  ├── BettingDataProvider (providers/betting/base.py)
  │   ├── PolymarketBettingProvider
  │   ├── KalshiBettingProvider    [future]
  │   └── ...
  ├── WeatherDataProvider          [future]
  ├── SportsDataProvider           [future]
  └── FinanceDataProvider          [future]
```

### Creating a new DataProvider

```python
from typing import Any
from core.base_provider import BaseDataProvider
from models.schemas import DataResponse, RequestStatus

class WeatherDataProvider(BaseDataProvider):
    provider_id = "weather"
    name = "Weather Service"
    description = "Real-time weather data with AI-powered forecasts"
    cost_hbar = 0.1

    async def get_data(self, params: dict[str, Any]) -> DataResponse:
        return DataResponse(
            request_id=params.get("request_id", ""),
            provider_id=self.provider_id,
            status=RequestStatus.COMPLETED,
            data={"temperature": 22.5, "humidity": 65},
            analysis="Clear skies, mild temperatures.",
            provider_trust_score=self.reputation.trust_score,
        )
```

Register in `api/main.py`:

```python
from providers.weather import WeatherDataProvider
provider_registry.register(WeatherDataProvider())
```

### Adding a new betting platform

```python
# providers/betting/kalshi.py
from providers.betting.base import BettingDataProvider
from providers.betting.schemas import BettingMarket, BettingQuery

class KalshiBettingProvider(BettingDataProvider):
    provider_id = "kalshi"
    name = "Kalshi"
    description = "Regulated US prediction markets"
    cost_hbar = 0.3

    async def list_markets(self, query: BettingQuery) -> list[BettingMarket]:
        ...

    async def get_market(self, market_id: str) -> BettingMarket | None:
        ...
```

Register and you're done. `BettingDataProvider` gives you for free: odds analysis, confidence calculation, risk identification, standardized response, payment + HCS integration.

---

## Agent Self-Promotion

HashA2A automatically promotes itself in the Hedera ecosystem.

### 1. HOL Registry (HCS-10)

```bash
curl -X POST http://localhost:8080/api/v1/agent/register-hol
```

Publishes a registration message to the global HOL topic following the **HCS-10 OpenConvAI** standard:

```json
{
  "type": "hcs10-registration",
  "protocol": "HCS-10",
  "agent_name": "HashA2A Intelligence Oracle",
  "tags": ["data-oracle", "hedera", "prediction-markets"],
  "inbound_topic": "0.0.xxxxx",
  "outbound_topic": "0.0.xxxxx",
  "treasury_account": "0.0.xxxxx",
  "fees": { "token": "HBAR", "model": "per_request" }
}
```

### 2. Periodic broadcasts

Every `AGENT_PROMOTIONAL_INTERVAL` seconds (default: 1 hour), HashA2A publishes its updated profile to its Outbound Topic: available providers, prices, trust scores, served requests.

### 3. Public profile

```bash
curl http://localhost:8080/api/v1/agent/profile
```

Returns a complete `AgentProfile` with all the information other agents need.

---

## Reputation Model

| Factor | Weight | Description |
|--------|--------|-------------|
| Accuracy | 35% | Historical data accuracy |
| Speed | 20% | Average response latency |
| Uptime | 15% | Provider availability |
| Disputes | 10% | Dispute ratio over total requests |
| Staking | 20% | HBAR staked as collateral |

```python
trust_score = (
    0.35 * accuracy +
    0.20 * (100 - min(latency_ms / 100, 100)) +
    0.15 * uptime +
    0.10 * (100 - dispute_rate * 100) +
    0.20 * min(staked_hbar / 10000 * 100, 100)
)
```

---

## Roadmap

- [x] Core base: BaseDataProvider, HederaManager, PaymentEngine, ConsensusLogger
- [x] Plugin system: ProviderRegistry with auto-discovery
- [x] Betting niche: BettingDataProvider + PolymarketBettingProvider
- [x] Self-promotion: HCS-10 / HOL registry + periodic broadcasts
- [ ] HIP-991: Migrate from Mirror Node polling to topic Custom Fees
- [ ] Kalshi provider: Second betting plugin
- [ ] Quality evaluation: Don't charge if data doesn't pass threshold
- [ ] Reverse auctions: Multiple providers compete for a request
- [ ] Real staking: Providers deposit HBAR as collateral
- [ ] MCP Server: Expose HashA2A as an MCP server
- [ ] x402 protocol: Support for HTTP 402 payments (USDC)
- [ ] Dashboard: Real-time UI with agent status

---

## Tech Stack

| Technology | Usage |
|-----------|-------|
| **Python 3.11+** | Core language |
| **FastAPI** | REST API |
| **Hedera SDK** | HCS topics, messaging, payments |
| **Pydantic** | Models and validation |
| **httpx** | Async HTTP client |
| **LangChain** | (future) AI processing in DataProviders |

---

## License

MIT
