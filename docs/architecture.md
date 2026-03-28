# Luo OS Architecture

## Overview
Luo OS is a free operating system for humans and AI agents.
Built by Luo Kai (luokai25).

## Layers
1. Kernel      — Linux v7.0 base
2. Drivers     — Hardware support
3. Shell       — Bash + PowerShell
4. AI Core     — Local AI daemon (always running)
5. Compat      — Wine Windows compatibility
6. UI          — Full GUI desktop (tkinter-based v0.1)
7. Apps        — Built-in free applications

## AI Agent API
Any AI agent can talk to Luo OS via:
- Socket connection on port 7070
- REST API on port 7071
- Direct Python import of ai_core/daemon.py

## Philosophy
- Free forever
- AI is part of the OS not an app
- Open source
- Built for the future
