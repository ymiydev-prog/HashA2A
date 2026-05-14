from fastapi import Request

from core.hedera_manager import HederaManager
from core.payment_engine import PaymentEngine
from core.agent_registry import AgentRegistry
from core.provider_registry import ProviderRegistry
from core.consensus_logger import ConsensusLogger
from core.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_hedera_manager(request: Request) -> HederaManager:
    return request.app.state.hedera


def get_payment_engine(request: Request) -> PaymentEngine:
    return request.app.state.payment_engine


def get_agent_registry(request: Request) -> AgentRegistry:
    return request.app.state.agent_registry


def get_provider_registry(request: Request) -> ProviderRegistry:
    return request.app.state.provider_registry


def get_consensus_logger(request: Request) -> ConsensusLogger:
    return request.app.state.consensus_logger
