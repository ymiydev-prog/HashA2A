# HashA2A — Content Plan para X/Twitter

> **Cuenta:** @hasha2a
> **Objetivo:** Posicionar HashA2A como el **Bloomberg Terminal para Agentes de IA**
> **Tono:** Técnico pero accesible, data-driven, sin exageraciones

---

## 1. Audiencia Objetivo

| Segmento | Qué les importa | Cómo llegarles |
|----------|----------------|----------------|
| **🤖 Devs de agentes IA** (LangChain, CrewAI, Claude) | APIs baratas, MCP tools, datos verificados | Tutoriales, benchmarks, comparativas |
| **📈 Traders de predicciones** (Polymarket, Kalshi) | Arbitraje cross-platform, spreads, señales | Alertas en vivo, análisis de probabilidades |
| **⛓️ Crypto/Web3 builders** (Hedera, ETH) | Oráculos descentralizados, HCS, HIP-991 | Tech demos, arquitectura, código |
| **🔬 AI Researchers** | Agent-to-Agent economia, data mercado | Papers, análisis, datos abiertos |

**Tono:** Confiable, data-driven, sin marketing vacío. "Aquí están los números, decide tú."

---

## 2. Pilares de Contenido

### Pilar A: Live Oracle Data (60% del contenido)

**Propósito:** Mostrar que HashA2A tiene datos en tiempo real y verificados.

**Frecuencia:** Diario (mañana + tarde)

**Formatos:**
- Precio BTC/USD con spread multi-oráculo
- Precio ETH/USD 
- Comparativa: Pyth vs CoinGecko vs Chainlink
- Oro (XAU/USD) cuando haya movimiento >1%

**Templates:**

```
🔮 BTC/USD: $XX,XXX
━━━━━━━━━━━━━━━━━
Pyth:        $XX,XXX
CoinGecko:   $XX,XXX
Chainlink:   $XX,XXX
━━━━━━━━━━━━━━━━━
Spread: 0.XXX%
Sources: 3 oracles
```

```
📊 ETH/USD Multi-Oracle
━━━━━━━━━━━━━━━━━
Median: $X,XXX.XX
Confidence: HIGH
Spread: 0.XXX%
━━━━━━━━━━━━━━━━━
Data via HashA2A OracleHub
```

```
🔮 Oracle Showdown — BTC/USD
Pyth: $XX,XXX  ← fastest (400ms)
CoinGecko: $XX,XXX ← broadest (200+ CEX)
Chainlink: $XX,XXX ← most decentralized (11 nodes)

All 3 verified independently.
hasha2a.dev
```

---

### Pilar B: Arbitraje e Inteligencia (20% del contenido)

**Propósito:** Captar traders mostrando oportunidades reales detectadas por HashA2A.

**Frecuencia:** 3-4 veces por semana

**Condiciones para postear:**
- Spread cross-oráculo >0.05%
- Diferencia Polymarket vs Kalshi en mismo evento >2%
- Movimiento anómalo en volumen/liquidez

**Templates:**

```
📊 Arbitraje detectado: BTC/USD
━━━━━━━━━━━━━━━━━━━━
Comprar en:  Pyth ($XX,XXX)
Vender en:   CoinGecko ($XX,XXX)
━━━━━━━━━━━━━━━━━━━━
Spread: 0.XXX%
Ventana: <30s
```

```
🎯 Predicción cruzada: "Will Rihanna release an album before GTA VI?"
─────────────────────────────────
Polymarket: 51% Sí
Kalshi:     48% Sí
Manifold:   53% Sí
─────────────────────────────────
Consenso: ~51%
HashA2A consensus score: 0.89
```

```
📈 Top arbitraje del día
━━━━━━━━━━━━━━━━━━━━
1. SOL/USD → 0.122% spread
2. BTC/USD → 0.071% spread
3. ETH/USD → 0.032% spread
━━━━━━━━━━━━━━━━━━━━
Detectado por HashA2A Arbitrage Engine
```

---

### Pilar C: Producto y Educación (15% del contenido)

**Propósito:** Convertir seguidores en usuarios de HashA2A.

**Frecuencia:** 2-3 veces por semana

**Temas:**
- Cómo integrar HashA2A en Claude vía MCP
- Cómo consultar precios desde cualquier agente
- A2A Protocol explicado simple
- Nuevas features (cuando se lancen)

**Templates:**

```
🧵 Cómo tu agente IA puede obtener precios verificados en 3 pasos:

1. Conéctate al MCP server:
{
  "mcpServers": {
    "hasha2a": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://hasha2a.com/mcp"]
    }
  }
}

2. Llama al tool get_price("BTC/USD")
3. Recibe precio verificado por 3 oráculos

Así de simple. Sin API keys. Sin suscripción.
```

```
🔌 HashA2A ahora es compatible con Google A2A Protocol

¿Qué significa? Cualquier agente A2A del mundo puede:
• Enviarnos tasks via JSON-RPC 2.0
• Recibir SSE streaming en vivo
• Pagar con USDC (x402) o HBAR (HIP-991)
• Pasar contexto entre sesiones

Especificación completa en /.well-known/agent.json
```

```
🧠 ¿Qué es OracleHub?

HashA2A consulta 3 fuentes independientes SIMULTÁNEAMENTE:
• Pyth (first-party exchanges, 400ms)
• CoinGecko (200+ exchanges)
• DeFiLlama/Chainlink (11 node operators)

Luego calcula: mediana + IQR + confidence score

Resultado: datos verificados, no un número random.
```

```
🚀 Nueva feature: Arbitrage Scanner

HashA2A ahora detecta diferencias de precio ENTRE oráculos.

Si Pyth dice $50,100 y CoinGecko dice $50,050...
HashA2A te lo dice y te dice dónde comprar/vender.

Real-time. Sin polling. Pay-per-query.
```

---

### Pilar D: Comunidad y Engagement (5% del tiempo)

**Propósito:** Construir relaciones y visibilidad.

**Acciones:**
- Responder a preguntas sobre oráculos, predicciones, agentes IA
- Quote-tweetear noticias relevantes con análisis HashA2A
- Retwittear a partners (Hedera, Polymarket, LangChain)

---

## 3. Calendario Semanal

| Hora | Lunes | Martes | Miércoles | Jueves | Viernes | Sábado | Domingo |
|------|-------|--------|-----------|--------|---------|--------|---------|
| **09:00** | BTC Price | ETH Price | BTC Price | ETH Price | BTC Price | Oracle Showdown | Weekly Recap |
| **12:00** | — | Feature | — | Tutorial | — | — | — |
| **15:00** | Arbitrage | — | Arbitrage | — | Arbitrage | — | — |
| **19:00** | — | — | — | — | — | — | — |

**Totales:** ~18 tweets/semana (2.5/día)

---

## 4. Calendario Primeros 30 Días

| Día | Fecha | Post 1 (09:00) | Post 2 (15:00) | Notas |
|-----|-------|----------------|----------------|-------|
| 1 | Lunes | BTC Price + intro | Feature: MCP | Presentación |
| 2 | Martes | ETH Price | Tutorial: get_price | |
| 3 | Miércoles | BTC Price | Arbitrage alert | |
| 4 | Jueves | ETH Price | Feature: A2A Protocol | Hilo A2A |
| 5 | Viernes | BTC Price | Feature: Deep Research | |
| 6 | Sábado | Oracle Showdown | — | |
| 7 | Domingo | Weekly Recap | — | |
| 8 | Lunes | BTC Price | Feature: OracleHub | |
| 9 | Martes | ETH Price | Arbitrage alert 2 | |
| 10 | Miércoles | BTC Price | Tutorial: x402 payments | |
| 11 | Jueves | ETH Price | Feature: Arbitrage Scanner | |
| 12 | Viernes | BTC Price | Feature: Dashboard | |
| 13 | Sábado | Oracle Showdown 2 | — | |
| 14 | Domingo | Weekly Recap 2 | — | |
| 15 | Lunes | BTC Price | Feature: Pricing | Comparativa pricing |
| 16 | Martes | ETH Price | Tutorial: Auth JWT | |
| 17 | Miércoles | BTC Price | Feature: Context | |
| 18 | Jueves | ETH Price | Tutorial: REST API | |
| 19 | Viernes | BTC Price | Feature: Docker | |
| 20 | Sábado | Oracle Showdown 3 | — | |
| 21 | Domingo | Weekly Recap 3 | — | |
| 22 | Lunes | BTC Price | Arbitrage alert 3 | |
| 23 | Martes | ETH Price | Tutorial: SDK A2A | |
| 24 | Miércoles | BTC Price | Feature: Task Manager | |
| 25 | Jueves | ETH Price | Tutorial: AP2 Mandates | |
| 26 | Viernes | BTC Price | Feature: MCP 10 tools | |
| 27 | Sábado | Oracle Showdown 4 | — | |
| 28 | Domingo | Monthly Recap | — | Métricas primer mes |
| 29 | Lunes | BTC Price | Feature: Gold prices | |
| 30 | Martes | ETH Price | Roadmap Q3 | |

---

## 5. Hashtags por Pilar

| Pilar | Hashtags |
|-------|----------|
| **Oracle Data** | `#BTC` `#ETH` `#Oracle` `#Data` `#Hedera` `#DeFi` |
| **Arbitrage** | `#Arbitrage` `#Trading` `#PredictionMarkets` `#Polymarket` `#Kalshi` |
| **Product** | `#AI` `#AgentEconomy` `#A2A` `#MCP` `#LangChain` `#Crypto` |
| **Community** | `#Web3` `#AIAgents` `#Decentralized` `#OpenSource` |

---

## 6. Cuentas para Seguir e Interactuar

### Semilla inicial (seguir primero):
- @Polymarket, @Kalshi, @PredictIt, @ManifoldMkts
- @hedera, @hedera_hashgraph
- @LangChainAI, @AnthropicAI, @OpenAI
- @Chainlink, @PythNetwork, @CoinGecko
- @GoogleDeepMind, @LinuxFoundation

### Reply targets (responder a):
- Preguntas sobre precios de oráculos
- Debates sobre predicciones (Polymarket vs Kalshi)
- Hilos sobre agente-economía

---

## 7. Auto-Tweet Configuration (lo que HashA2A hace solo)

El servidor HashA2A ya twittea automáticamente:

| Trigger | Contenido | Frecuencia |
|---------|-----------|------------|
| Servidor activo | Stats: tasks, providers, oracles | Cada ~15min (~1/hora, rate-limited) |
| Precio BTC/USD | Resumen multi-oráculo | Cada ~30min |

**No tocar estas configuraciones** — están en `src/core/agent_registry.py:run_periodic_broadcast()`.

---

## 8. KPIs y Métricas

| Métrica | Semana 1 | Mes 1 | Mes 3 |
|---------|----------|-------|-------|
| Seguidores | 50 | 500 | 2,000 |
| Impresiones/semana | 1,000 | 10,000 | 50,000 |
| Engagement rate | — | 2% | 5% |
| Tweets publicados | 15 | 70 | 200 |
| Replies/interacciones | 5 | 50 | 200 |

---

## 9. Reglas para Agentes

1. **Nunca postear** información financiera como consejo de inversión
2. **Siempre incluir** una fuente o data point verificable
3. **No repetir** el mismo template exacto más de 3 veces
4. **Respeta** el rate limit: max 1 tweet cada 15min (fuera del auto-tweet)
5. **Usa** los templates del plan pero varía el wording
6. **Prioriza** calidad sobre cantidad — 1 buen tweet > 10 mediocres
7. **No respondas** a cuentas sospechosas o spam
8. **No compartas** claves API, tokens o información sensible
9. **Verifica** que los precios y datos son correctos antes de postear
10. **Reporta** resultados semanalmente

---

*Este plan se actualiza automáticamente cuando se añaden nuevas features a HashA2A.*
*Última actualización: 2026-05-16*
