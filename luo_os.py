#!/usr/bin/env python3
"""
Luo OS v0.1 — Main Launcher
The OS that is free for all — humans and AI agents
Created by Luo Kai (luokai25)
"""

import tkinter as tk
import threading
import subprocess
import sys
import os
from datetime import datetime

# Add all modules to path
sys.path.insert(0, os.path.dirname(__file__))

class LuoOSBoot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Luo OS v0.1 — Booting...")
        self.root.configure(bg="#0a0a1a")
        self.root.geometry("800x500")
        self.root.resizable(False, False)
        self.boot_steps = [
            ("Initializing Luo OS kernel...",        0.5),
            ("Loading hardware drivers...",           0.5),
            ("Starting AI Core daemon...",            0.8),
            ("Mounting filesystems...",               0.4),
            ("Loading Windows compatibility...",      0.5),
            ("Starting shell environment...",         0.4),
            ("Launching desktop GUI...",              0.6),
            ("Luo OS ready.",                         0.3),
        ]
        self.setup_boot_screen()

    def setup_boot_screen(self):
        # Logo
        tk.Label(
            self.root,
            text="LUO OS",
            font=("Courier", 64, "bold"),
            fg="#00ffcc",
            bg="#0a0a1a"
        ).pack(pady=30)

        tk.Label(
            self.root,
            text="Free OS for Humans & AI Agents — v0.1",
            font=("Courier", 13),
            fg="#ffffff",
            bg="#0a0a1a"
        ).pack()

        tk.Label(
            self.root,
            text="by Luo Kai (luokai25)",
            font=("Courier", 11),
            fg="#555577",
            bg="#0a0a1a"
        ).pack(pady=5)

        # Progress bar
        self.progress_frame = tk.Frame(self.root, bg="#0a0a1a")
        self.progress_frame.pack(pady=20, fill="x", padx=80)

        self.progress_bar = tk.Canvas(
            self.progress_frame,
            height=6,
            bg="#111133",
            highlightthickness=0
        )
        self.progress_bar.pack(fill="x")

        self.progress_fill = self.progress_bar.create_rectangle(
            0, 0, 0, 6,
            fill="#00ffcc",
            outline=""
        )

        # Boot log
        self.log = tk.Label(
            self.root,
            text="Starting Luo OS...",
            font=("Courier", 11),
            fg="#00ffcc",
            bg="#0a0a1a"
        )
        self.log.pack(pady=10)

        # Mode selector
        mode_frame = tk.Frame(self.root, bg="#0a0a1a")
        mode_frame.pack(pady=20)

        tk.Label(
            mode_frame,
            text="Boot Mode:",
            font=("Courier", 11),
            fg="#ffffff",
            bg="#0a0a1a"
        ).pack(side="left", padx=10)

        self.mode = tk.StringVar(value="human")

        for text, val in [("Human Mode", "human"), ("AI Agent Mode", "ai"), ("Safe Mode", "safe")]:
            tk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.mode,
                value=val,
                font=("Courier", 11),
                fg="#00ffcc",
                bg="#0a0a1a",
                selectcolor="#111133",
                activebackground="#0a0a1a",
                activeforeground="#00ffcc"
            ).pack(side="left", padx=10)

        # Boot button
        tk.Button(
            self.root,
            text="⚡ BOOT LUO OS",
            font=("Courier", 14, "bold"),
            bg="#00ffcc",
            fg="#0a0a1a",
            relief="flat",
            width=20,
            command=self.start_boot
        ).pack(pady=10)

    def start_boot(self):
        thread = threading.Thread(target=self.boot_sequence)
        thread.daemon = True
        thread.start()

    def boot_sequence(self):
        import time
        total = len(self.boot_steps)
        bar_width = 640

        for i, (msg, delay) in enumerate(self.boot_steps):
            self.log.config(text=f"[ OK ] {msg}")
            progress = int((i + 1) / total * bar_width)
            self.progress_bar.coords(self.progress_fill, 0, 0, progress, 6)
            time.sleep(delay)

        # Launch desktop
        self.root.after(0, self.launch_desktop)

    def launch_desktop(self):
        self.root.destroy()
        mode = self.mode.get()

        if mode == "ai":
            # AI agent mode — launch AI core directly
            os.system("python3 ai_core/daemon.py")
        elif mode == "safe":
            # Safe mode — minimal shell
            os.system("bash shell/luo_shell.sh")
        else:
            # Human mode — full desktop
            from ui.window_manager import LuoDesktop
            desktop = LuoDesktop()
            desktop.run()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    boot = LuoOSBoot()
    boot.run()
