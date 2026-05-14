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
from api.main import app

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8080, reload=True)
