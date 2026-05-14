#!/usr/bin/env python3
"""
HashA2A — Runner script.
Starts the FastAPI server and initializes the Hedera agent.
"""

import uvicorn
from core.config import Settings

if __name__ == "__main__":
    settings = Settings()
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
