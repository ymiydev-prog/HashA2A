# 🚀 HashA2A Future Roadmap

Este documento detalla las próximas fases de desarrollo para **HashA2A — The Agent-to-Agent Intelligence Layer**. El objetivo es evolucionar de un mercado de datos centralizado a una red de oráculos descentralizada y automatizada.

---

## 📅 Fase 1: Integración y Automatización (Q3 2026)
*Enfoque: Facilitar el consumo de HashA2A para desarrolladores "low-code".*

- [ ] **n8n Workflow Hub**: 
    - Crear carpeta `.n8n/workflows/` con templates listos para usar.
    - **Workflow A**: Alerta de arbitraje (HashA2A MCP → Telegram/Slack).
    - **Workflow B**: Auditoría de pagos (HCS Topic Monitor → Google Sheets).
- [ ] **SDK de Cliente (Python/JS)**:
    - Crear un paquete ligero para que otros agentes se conecten a HashA2A en 3 líneas de código.
- [ ] **A2A Protocol v1.1**:
    - Implementar soporte completo para **SSE (Server-Sent Events)** en todas las rutas de procesamiento largo para evitar timeouts.

---

## 🧠 Fase 2: Reputación y Confianza On-Chain (Q4 2026)
*Enfoque: Convertir la "confianza" en un activo verificable en Hedera.*

- [ ] **HCS Reputation Ledger**:
    - Cada respuesta de un provider genera un "hash de veracidad" en un tópico de auditoría dedicado.
    - Implementar un sistema de **Scorecard** público basado en la precisión histórica frente al resultado real (Backtesting).
- [ ] **Staking & Slashing (Simulado)**:
    - Los proveedores deben "estakear" HBAR para operar. Si entregan datos erróneos (detectado por consenso), pierden una porción del stake.
- [ ] **HIP-991 Dynamic Pricing**:
    - Ajustar el costo de la consulta basado en la reputación del proveedor en tiempo real.

---

## ⚡ Fase 3: Optimización de Rendimiento (Q1 2027)
*Enfoque: Reducir la latencia para aplicaciones de alta frecuencia.*

- [ ] **Ultra-Low Latency AI**:
    - Integrar **Groq** o **DeepSeek** para reducir el tiempo de análisis de mercado de ~2s a <300ms.
- [ ] **Caché Inteligente (Redis)**:
    - Implementar una capa de caché para feeds de precios de oráculos (Pyth/CoinGecko) con TTL de 5s para reducir llamadas a APIs externas.
- [ ] **Batch Processing**:
    - Permitir consultas de múltiples activos en un solo mensaje HCS para optimizar costos de red.

---

## 🌐 Fase 4: HashA2A Network (Q2 2027 y más allá)
*Enfoque: Descentralización total y gobernanza.*

- [ ] **Decentralized Oracle Network (DON)**:
    - Permitir que terceros corran sus propios nodos de HashA2A y contribuyan al consenso de precios.
- [ ] **Gobernanza A2A**:
    - Implementar votaciones vía HCS para decidir qué nuevos proveedores de datos añadir a la plataforma.
- [ ] **Integración x402 Cross-Chain**:
    - Expandir los pagos en USDC de Base a otras redes (Optimism, Arbitrum, Hedera USDC).

---

> [!TIP]
> Este plan es una guía evolutiva. Se priorizarán las tareas basadas en la adopción de la comunidad y el feedback de los agentes en el HOL Registry.
