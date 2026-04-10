#!/bin/bash
# Luo OS — Quick Start Script
# Starts all services in the background

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "  Luo OS — Quick Start"
echo "═══════════════════════════════════════════════════════════════"

# Check Python
PYTHON="${PYTHON:-$(which python3)}"
if [ ! -x "$PYTHON" ]; then
    echo "✗ Python3 not found"
    exit 1
fi

# Check if Ollama is running
echo ""
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "⚠ Ollama not detected. Start with: ollama serve"
    echo "  Continuing anyway..."
fi

# Create data directories
mkdir -p ~/.luo_os/chroma
mkdir -p ~/.luo_os/luokai
mkdir -p ~/.luo_os/logs

# Start options
echo ""
echo "Select startup mode:"
echo "  1) Chat only (interactive)"
echo "  2) Web server only"
echo "  3) Evolution engine (background)"
echo "  4) All services"
echo "  5) Voice interface"
echo ""
read -p "Choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "Starting chat mode..."
        $PYTHON luo_cli.py chat
        ;;
    2)
        echo ""
        echo "Starting web server on port 3000..."
        echo "Open: http://localhost:3000"
        $PYTHON luo_server.py
        ;;
    3)
        echo ""
        echo "Starting evolution engine in background..."
        nohup $PYTHON luo_cli.py evolution > ~/.luo_os/logs/evolution.log 2>&1 &
        echo "PID: $!"
        echo "Logs: ~/.luo_os/logs/evolution.log"
        ;;
    4)
        echo ""
        echo "Starting all services..."

        # Start web server in background
        nohup $PYTHON luo_server.py > ~/.luo_os/logs/server.log 2>&1 &
        SERVER_PID=$!
        echo "  Server PID: $SERVER_PID (port 3000)"

        # Start evolution in background
        nohup $PYTHON luo_cli.py evolution --interval 300 > ~/.luo_os/logs/evolution.log 2>&1 &
        EVO_PID=$!
        echo "  Evolution PID: $EVO_PID"

        # Start chat
        echo ""
        echo "Starting interactive chat..."
        $PYTHON luo_cli.py chat
        ;;
    5)
        echo ""
        echo "Starting voice interface..."
        echo "Say 'Luo' to wake me up."
        $PYTHON luo_cli.py voice
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac