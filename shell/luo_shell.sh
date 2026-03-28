#!/bin/bash
# Luo OS Shell — by Luo Kai (luokai25)

echo "================================"
echo "  LUO OS v0.1 — Luo Shell"
echo "  Free for Humans & AI Agents"
echo "================================"

while true; do
    read -p "luo@luoos:~$ " cmd
    case $cmd in
        "ai")        python3 ~/ai_core/daemon.py ;;
        "desktop")   python3 ~/ui/window_manager.py ;;
        "info")      uname -a ;;
        "help")      echo "Commands: ai, desktop, info, exit" ;;
        "exit")      echo "Goodbye from Luo OS!"; break ;;
        *)           eval "$cmd" ;;
    esac
done
