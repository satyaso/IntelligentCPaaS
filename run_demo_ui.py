#!/usr/bin/env python3
"""
Startup script for Applied-Agentic AI AWS CPaaS Demo Web UI.

Run this to start the local web server for business users.

USAGE:
    python3 run_demo_ui.py

TO STOP:
    Press Ctrl+C in the terminal
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_cpaas_demo.web.app import app

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🚀 Starting Applied-Agentic AI AWS CPaaS Demo Web UI")
    print("=" * 80)
    print("\n📍 Server will be available at: http://localhost:8888")
    print("\n⚠️  TO STOP THE SERVER: Press Ctrl+C")
    print("\n" + "=" * 80 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=8888)
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped by user (Ctrl+C)")
        print("=" * 80 + "\n")
