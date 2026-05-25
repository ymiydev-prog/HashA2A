import json
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import Settings


PROVIDER_CONTEXTS = {
    "polymarket": (
        "Polymarket is a decentralized prediction market platform (Polygon). "
        "Markets have outcomes (Yes/No) with prices ranging 0-1 cent. "
        "Analyze the probability implied by the price and any significant changes."
    ),
    "kalshi": (
        "Kalshi is a CFTC-regulated US prediction market. "
        "Markets have Yes/No binary outcomes with prices in dollars ($0.01-$0.99). "
        "Analyze the implied probability and market movement."
    ),
    "predictit": (
        "PredictIt is a US academic prediction market run by Victoria University. "
        "Markets have binary or multi-outcome contracts with prices in cents ($0.01-$0.99). "
        "Analyze the implied probability and volume trends."
    ),
    "manifold": (
        "Manifold Markets is a play-money prediction market platform. "
        "Markets can be binary, multiple choice, or free response. "
        "For binary markets, price represents probability (0-100%). "
        "Analyze the market consensus and trader activity."
    ),
    "hyperliquid": (
        "Hyperliquid HIP-4 is an on-chain binary outcome market protocol on HyperCore. "
        "Markets are fully-collateralized YES/NO binary contracts that settle to 0 or 1 "
        "against an authorized oracle at expiry. Prices represent implied probability. "
        "Covers crypto price targets and CPI forecasts. "
        "Trades on an on-chain central limit order book (CLOB) with USDH settlement. "
        "Analyze on-chain liquidity, order book depth, and implied probabilities."
    ),
    "aggregated": (
        "This is aggregated intelligence from MULTIPLE prediction market platforms: "
        "Polymarket (decentralized), Kalshi (CFTC-regulated), PredictIt (academic), "
        "Manifold (play-money), and Hyperliquid HIP-4 (on-chain CLOB). "
        "Data has been cross-validated across sources. "
        "Compare prices across platforms, identify arbitrage opportunities, "
        "and assess the overall market consensus. When sources agree, confidence is high. "
        "When they diverge, highlight the spread and possible reasons."
    ),
}

ANALYSIS_PROMPT = """You are a financial analysis AI specializing in prediction markets.
Given the market data below, provide a concise analysis covering:

1. Current market probabilities / prices
2. Market sentiment and direction
3. Key observations (volume, spread, movement)
4. Confidence assessment based on available data

Keep analysis concise (3-5 sentences). Focus on actionable insights."""


class AIAnalyzer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._llm: ChatOpenAI | None = None

    def _get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.settings.langchain_model,
                temperature=self.settings.langchain_temperature,
                api_key=self.settings.openai_api_key,
            )
        return self._llm

    def analyze(self, provider_id: str, data: dict[str, Any] | None) -> str | None:
        if not data:
            return None

        api_key = self.settings.openai_api_key
        if not api_key:
            return None

        context = PROVIDER_CONTEXTS.get(provider_id, "")
        data_str = json.dumps(data, indent=2, default=str)[:3000]

        try:
            llm = self._get_llm()
            messages = [
                SystemMessage(content=f"{ANALYSIS_PROMPT}\n\nProvider context: {context}"),
                HumanMessage(content=f"Market data:\n{data_str}"),
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            return f"[Analysis unavailable: {e}]"
