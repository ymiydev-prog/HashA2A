from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    hedera_operator_id: str = ""
    hedera_operator_key: str = ""
    hedera_network: str = "testnet"

    treasury_account: str = ""
    treasury_private_key: str = ""

    mirror_node_url: str = "https://testnet.mirrornode.hedera.com"
    hol_registry_topic: str = "0.0.29640405"

    payment_polling_interval: float = 5.0
    payment_ttl_seconds: int = 300
    request_expiry_seconds: int = 3600

    openai_api_key: str | None = None
    langchain_model: str = "gpt-4o-mini"
    langchain_temperature: float = 0.3

    agent_name: str = "HashA2A Intelligence Oracle"
    agent_description: str = "Modular data oracle where agents buy AI-processed intelligence via HBAR micropayments"
    agent_version: str = "0.1.0"
    agent_tags: list[str] = ["data-oracle", "intelligence", "hedera", "ai", "prediction-markets"]
    agent_promotional_interval: int = 3600

    api_host: str = "0.0.0.0"
    api_port: int = 8080

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
