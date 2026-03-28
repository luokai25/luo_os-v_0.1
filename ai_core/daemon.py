#!/usr/bin/env python3
"""
Luo OS AI Core Daemon
Local AI agent built into the OS — created by Luo Kai (luokai25)
"""

import os
import json
import time
import subprocess
from datetime import datetime

class LuoAI:
    def __init__(self):
        self.name = "Luo AI"
        self.version = "0.1"
        self.memory = []
        self.running = True
        print(f"[{self.name} v{self.version}] Starting up...")

    def think(self, input_text):
        """Process input and return response"""
        input_lower = input_text.lower()
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Log to memory
        self.memory.append({"time": timestamp, "input": input_text})

        # Basic OS commands
        if "open terminal" in input_lower:
            return self.open_terminal()
        elif "list files" in input_lower:
            return self.list_files()
        elif "system info" in input_lower:
            return self.system_info()
        elif "time" in input_lower:
            return f"Current time: {timestamp}"
        elif "memory" in input_lower:
            return f"I remember {len(self.memory)} interactions so far."
        elif "help" in input_lower:
            return self.help()
        elif "shutdown" in input_lower:
            self.running = False
            return "Luo OS shutting down..."
        else:
            return f"I heard you say: '{input_text}'. I am still learning."

    def open_terminal(self):
        subprocess.Popen(["xterm"])
        return "Opening terminal..."

    def list_files(self):
        files = os.listdir(".")
        return f"Files: {', '.join(files)}"

    def system_info(self):
        info = os.uname()
        return f"System: {info.sysname} {info.release} | Machine: {info.machine}"

    def help(self):
        return """
Luo AI Commands:
- open terminal    → open a terminal window
- list files       → list files in current directory  
- system info      → show system information
- time             → show current time
- memory           → show interaction count
- shutdown         → shutdown Luo OS
        """

    def run(self):
        """Main loop"""
        print(f"[Luo AI] Ready. Type 'help' for commands.")
        while self.running:
            try:
                user_input = input("\n[You] → ")
                if user_input.strip():
                    response = self.think(user_input)
                    print(f"[Luo AI] → {response}")
            except KeyboardInterrupt:
                print("\n[Luo AI] Interrupted.")
                break

if __name__ == "__main__":
    ai = LuoAI()
    ai.run()
