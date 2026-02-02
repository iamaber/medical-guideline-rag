#!/bin/bash

# Development startup script for Medical Advisor System
echo "🛠️ Starting Medical Advisor System in Development Mode..."

# Set development environment variables
export ENVIRONMENT="development"
export LOG_LEVEL="DEBUG"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOL
# Medical Advisor Environment Variables
GEMINI_API_KEY=your_gemini_api_key_here
NCBI_EMAIL=your_email@example.com
NCBI_API_KEY=your_ncbi_api_key_here

# Optional: Development settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOL
    echo "⚠️ Please edit .env file with your API keys before continuing"
    exit 1
fi

# Load environment variables
source .env

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
uv sync

# Install development dependencies
echo "🛠️ Installing development tools..."
pip install black isort flake8 pytest

# Download spaCy model if not exists
if ! python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo "🧠 Downloading spaCy language model..."
    python -m spacy download en_core_web_sm
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/vector_store
mkdir -p logs
mkdir -p tests

# Run tests if they exist
if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
    echo "🧪 Running tests..."
    python -m pytest tests/ -v
fi

# Check data availability
echo "📊 Checking data availability..."
if [ ! -f "data/drug_db/medex_URL.json" ]; then
    echo "⚠️ WARNING: Drug database not found at data/drug_db/medex_URL.json"
fi

if [ ! "$(ls -A data/processed/ 2>/dev/null)" ]; then
    echo "⚠️ WARNING: No processed data found in data/processed/"
    echo "📥 The system will work but may have limited search capabilities"
fi

# Check if services are already running
echo "🔍 Checking for existing services..."

# Check if API is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server is already running on http://localhost:8000"
    API_RUNNING=true
else
    API_RUNNING=false
fi

# Check if Streamlit is already running
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Streamlit frontend is already running on http://localhost:8501"
    UI_RUNNING=true
else
    UI_RUNNING=false
fi

# Start API server if not running
if [ "$API_RUNNING" = false ]; then
    echo "🌐 Starting API server in development mode..."
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug &
    API_PID=$!
    
    # Wait for API to start
    echo "⏳ Waiting for API to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API server is running on http://localhost:8000"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    # Final check if API is running
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "❌ Failed to start API server after 30 seconds"
        echo "📝 Check logs for errors"
        kill $API_PID 2>/dev/null
        exit 1
    fi
fi

echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 API Health Check: http://localhost:8000/health"
echo "📊 System Stats: http://localhost:8000/stats"

# Start Streamlit frontend if not running
if [ "$UI_RUNNING" = false ]; then
    echo "🎨 Starting Python Streamlit frontend in development mode..."
    echo "🌐 Frontend will be available at: http://localhost:8501"
    
    # Dependencies are managed by uv and pyproject.toml
    echo "ℹ️  Using dependencies from pyproject.toml (managed by uv)"
    
    # Start the Streamlit development server
    echo "🚀 Starting Streamlit..."
    cd ui && streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
    UI_PID=$!
    cd ..
else
    echo "ℹ️  Streamlit frontend is already running"
fi

echo ""
echo "🎉 Services are ready!"
echo "📊 API: http://localhost:8000"
echo "🖥️  Frontend: http://localhost:8501"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop services (if started by this script)"

# Set up cleanup on exit for services started by this script
if [ -n "$API_PID" ] || [ -n "$UI_PID" ]; then
    trap "echo '🛑 Shutting down development services...'; kill $API_PID $UI_PID 2>/dev/null; exit" INT TERM EXIT
    # Keep script running
    wait
fi
