#!/usr/bin/env python3
"""
Launcher script for the Czech Real Estate Bargain Finder application.
Starts the FastAPI server with Uvicorn.
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    
    print("=" * 60)
    print("🚀 Czech Real Estate Bargain Finder (BytyBargain)")
    print(f"🌐 Application running at: http://{host}:{port}")
    print("=" * 60)
    
    uvicorn.run("backend.app:app", host=host, port=port, reload=True)
