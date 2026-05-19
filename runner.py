#!/usr/bin/env python3
"""
HashA2A — Root runner.
Adds src/ to Python path and starts the FastAPI server.
"""

import sys
import os

src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, os.path.abspath(src_path))

import uvicorn
from core.config import Settings

if __name__ == "__main__":
    settings = Settings()
    port = int(os.environ.get("PORT", settings.api_port))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
