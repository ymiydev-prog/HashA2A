from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from enum import Enum


class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"


class BettingOutcome(BaseModel):
    name: str
    price: float | None = None
    volume: float | None = None
    token_id: str | None = None


class BettingMarket(BaseModel):
    platform: str
    market_id: str
    title: str
    description: str | None = None
    status: MarketStatus = MarketStatus.UNKNOWN
    outcomes: list[BettingOutcome] = []
    volume: float = 0.0
    liquidity: float = 0.0
    open_time: str | None = None
    close_time: str | None = None
    resolution_time: str | None = None
    resolution_outcome: str | None = None
    category: str | None = None
    tags: list[str] = []
    url: str | None = None
    raw_data: dict[str, Any] | None = None


class BettingAnalysis(BaseModel):
    market_id: str
    platform: str
    title: str
    market_implied_probabilities: dict[str, float]
    market_confidence: str
    risk_factors: list[str] = []
    reasoning: str = ""
    edge: float | None = None


class BettingQuery(BaseModel):
    query: str | None = Field(default=None, description="Search term for markets")
    market_ids: list[str] | None = Field(default=None, description="Specific market IDs")
    limit: int = Field(default=10, ge=1, le=100)
    include_analysis: bool = True
    category: str | None = None
    status: str | None = None


class BettingResponse(BaseModel):
    platform: str
    markets: list[BettingMarket]
    analysis: list[BettingAnalysis] | None = None
    total_found: int
    processing_time_ms: float | None = None
