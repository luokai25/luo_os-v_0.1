#!/bin/bash
# Luo OS Startup Script
# Starts all services and the desktop
# Created by Luo Kai (luokai25)

echo "╔══════════════════════════════════════╗"
echo "║        LUO OS v0.1 STARTING          ║"
echo "║  Free OS for Humans & AI Agents      ║"
echo "╚══════════════════════════════════════╝"

DIR="$(cd "$(dirname "$0")" && pwd)"

# Start Ollama
echo "[1/4] Starting Ollama AI..."
ollama serve &>/tmp/ollama.log &
sleep 3

# Start Socket API (port 7070)
echo "[2/4] Starting AI Agent API (port 7070)..."
python3 $DIR/ai_core/agent_api.py &>/tmp/luo_agent_api.log &

# Start REST API (port 7071)
echo "[3/4] Starting REST API (port 7071)..."
python3 $DIR/ai_core/rest_api.py &>/tmp/luo_rest_api.log &

sleep 1

# Start Desktop
echo "[4/4] Launching Desktop..."
python3 $DIR/luo_os.py

echo "Luo OS stopped."
