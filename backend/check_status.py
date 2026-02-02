#!/usr/bin/env python3
"""
Medical Advisor System Status Check
Run this to verify your system is ready to use.
"""

import sys
import os
import requests
from pathlib import Path


def check_environment():
    """Check if environment is properly set up."""
    print("🔍 Checking Medical Advisor System Status...\n")

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Not in medical-guideline-rag directory")
        return False

    # Check API status
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Server: Running")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Services: {data.get('services', 'unknown')}")
        else:
            print("⚠️ API Server: Responding but unhealthy")
    except requests.ConnectionError:
        print("❌ API Server: Not running")
        print("   Start with: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ API Server: Error - {e}")

    # Check frontend status
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: Running on http://localhost:8501")
        else:
            print("⚠️ Frontend: Responding but may have issues")
    except requests.ConnectionError:
        print("❌ Frontend: Not running")
        print(
            "   Start with: uv run streamlit run ui/streamlit_app.py --server.port 8501"
        )
    except Exception as e:
        print(f"❌ Frontend: Error - {e}")

    # Check data availability
    drug_db_path = Path("data/drug_db/medex_URL.json")
    if drug_db_path.exists():
        print("✅ Drug Database: Available")
    else:
        print("⚠️ Drug Database: Not found")

    processed_data = Path("data/processed")
    if processed_data.exists() and list(processed_data.glob("*.json")):
        print("✅ Medical Literature: Available")
        print(f"   Files: {len(list(processed_data.glob('*.json')))}")
    else:
        print("⚠️ Medical Literature: Limited or not found")

    # Check vector index
    vector_index = Path("data/vector_index.faiss")
    if vector_index.exists():
        print("✅ Vector Search Index: Available")
    else:
        print("⚠️ Vector Search Index: Not found (will be created on first run)")

    print(f"\n📊 System Summary:")
    print(f"   🌐 API Documentation: http://localhost:8000/docs")
    print(f"   🏥 Medical Advisor UI: http://localhost:8501")
    print(f"   💾 Data Directory: {Path('data').absolute()}")

    return True


if __name__ == "__main__":
    try:
        check_environment()
    except KeyboardInterrupt:
        print("\n👋 Status check cancelled")
    except Exception as e:
        print(f"\n❌ Error during status check: {e}")
        sys.exit(1)
