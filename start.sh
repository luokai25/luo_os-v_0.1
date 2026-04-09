#!/bin/bash
echo ""
echo "  ██╗     ██╗   ██╗ ██████╗"
echo "  ██║     ██║   ██║██╔═══██╗   LuoOS v1.0"
echo "  ██║     ██║   ██║██║   ██║   by Luo Kai"
echo "  ███████╗╚██████╔╝╚██████╔╝"
echo ""

# Install deps if needed
if ! python3 -c "import flask" 2>/dev/null; then
  echo "Installing dependencies..."
  pip install flask flask-cors requests pyttsx3 SpeechRecognition -q
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "✅ Ollama running"
else
  echo "⚠️  Ollama not running. For full AI: ollama serve && ollama pull mistral"
fi

echo ""
echo "🚀 Starting LuoOS..."
echo "   Open: http://localhost:3000"
echo ""
python3 luo_server.py
