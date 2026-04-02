#!/bin/bash
# Luo OS — Start Script
# Built by Abd El-Rahman Abbas (Mr. Kai)

GR='\033[92m'; YL='\033[93m'; CY='\033[96m'; B='\033[1m'; R='\033[0m'; DIM='\033[2m'
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir -p .luo_logs

echo -e "${CY}${B}"
echo "  _     _   _  ___       ___  ___ "
echo " | |   | | | |/ _ \     / _ \/ __|"
echo " | |   | | | | | | |   | | | \__ \"
echo " |_|   |___|_|\___/     \___/|___/"
echo -e "${R}${DIM}  v0.1 — Free OS for Humans & AI Agents${R}"
echo ""

# try supervisor first (proper process manager)
if command -v supervisord &>/dev/null; then
    echo -e "${GR}Starting with Supervisor (process manager)...${R}"
    supervisord -c supervisor.conf
else
    echo -e "${YL}Supervisor not found — using basic boot...${R}"
    python3 luo_init.py
fi
