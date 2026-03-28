#!/usr/bin/env python3
"""
Luo OS Window Manager
Full GUI desktop for humans and AI agents — by Luo Kai (luokai25)
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import json
import os
from datetime import datetime

class LuoDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Luo OS v0.1")
        self.root.configure(bg="#0a0a1a")
        self.windows = []
        self.setup_desktop()
        self.setup_taskbar()
        self.setup_icons()
        self.setup_ai_panel()

    def setup_desktop(self):
        """Main desktop background"""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.resizable(True, True)

        # Desktop label
        title = tk.Label(
            self.root,
            text="LUO OS v0.1",
            font=("Courier", 48, "bold"),
            fg="#00ffcc",
            bg="#0a0a1a"
        )
        title.place(relx=0.5, rely=0.4, anchor="center")

        subtitle = tk.Label(
            self.root,
            text="Free OS for Humans & AI Agents — by Luo Kai",
            font=("Courier", 14),
            fg="#ffffff",
            bg="#0a0a1a"
        )
        subtitle.place(relx=0.5, rely=0.47, anchor="center")

    def setup_taskbar(self):
        """Bottom taskbar"""
        self.taskbar = tk.Frame(
            self.root,
            bg="#111133",
            height=50
        )
        self.taskbar.pack(side="bottom", fill="x")

        # Start button
        start_btn = tk.Button(
            self.taskbar,
            text="⚡ LUO OS",
            font=("Courier", 12, "bold"),
            bg="#00ffcc",
            fg="#0a0a1a",
            relief="flat",
            command=self.open_start_menu
        )
        start_btn.pack(side="left", padx=10, pady=5)

        # Clock
        self.clock_label = tk.Label(
            self.taskbar,
            text="",
            font=("Courier", 12),
            fg="#00ffcc",
            bg="#111133"
        )
        self.clock_label.pack(side="right", padx=10)
        self.update_clock()

    def setup_icons(self):
        """Desktop icons"""
        icons = [
            ("🖥️ Terminal", self.open_terminal),
            ("🤖 Luo AI", self.open_ai_window),
            ("📁 Files", self.open_files),
            ("⚙️ Settings", self.open_settings),
        ]
        for i, (name, cmd) in enumerate(icons):
            btn = tk.Button(
                self.root,
                text=name,
                font=("Courier", 11),
                bg="#111133",
                fg="#00ffcc",
                relief="flat",
                width=14,
                command=cmd
            )
            btn.place(x=30, y=50 + i * 80)

    def setup_ai_panel(self):
        """AI assistant side panel"""
        self.ai_panel = tk.Frame(
            self.root,
            bg="#111133",
            width=300
        )
        self.ai_panel.place(relx=1.0, rely=0.0, anchor="ne", relheight=0.9)

        tk.Label(
            self.ai_panel,
            text="🤖 Luo AI",
            font=("Courier", 14, "bold"),
            fg="#00ffcc",
            bg="#111133"
        ).pack(pady=10)

        self.ai_output = tk.Text(
            self.ai_panel,
            width=35,
            height=20,
            bg="#0a0a1a",
            fg="#00ffcc",
            font=("Courier", 10),
            relief="flat"
        )
        self.ai_output.pack(padx=10, pady=5)
        self.ai_output.insert("end", "Luo AI ready...\n")

        self.ai_input = tk.Entry(
            self.ai_panel,
            width=35,
            bg="#0a0a1a",
            fg="#ffffff",
            font=("Courier", 11),
            relief="flat"
        )
        self.ai_input.pack(padx=10, pady=5)
        self.ai_input.bind("<Return>", self.send_to_ai)

        tk.Button(
            self.ai_panel,
            text="Send →",
            font=("Courier", 11),
            bg="#00ffcc",
            fg="#0a0a1a",
            relief="flat",
            command=lambda: self.send_to_ai(None)
        ).pack(pady=5)

    def send_to_ai(self, event):
        msg = self.ai_input.get()
        if msg.strip():
            self.ai_output.insert("end", f"\nYou: {msg}\n")
            self.ai_output.insert("end", f"Luo AI: Processing '{msg}'...\n")
            self.ai_output.see("end")
            self.ai_input.delete(0, "end")

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S  %d/%m/%Y")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def open_terminal(self):
        win = tk.Toplevel(self.root, bg="#0a0a1a")
        win.title("Terminal")
        win.geometry("600x400")
        tk.Label(win, text="Luo OS Terminal", fg="#00ffcc", bg="#0a0a1a", font=("Courier", 12, "bold")).pack(pady=5)
        text = tk.Text(win, bg="#0a0a1a", fg="#00ffcc", font=("Courier", 11))
        text.pack(fill="both", expand=True)
        text.insert("end", "luo@luoos:~$ ")

    def open_ai_window(self):
        win = tk.Toplevel(self.root, bg="#0a0a1a")
        win.title("Luo AI")
        win.geometry("500x400")
        tk.Label(win, text="🤖 Luo AI Core v0.1", fg="#00ffcc", bg="#0a0a1a", font=("Courier", 14, "bold")).pack(pady=10)
        tk.Label(win, text="Local AI Agent — Always Free", fg="#ffffff", bg="#0a0a1a", font=("Courier", 11)).pack()

    def open_files(self):
        win = tk.Toplevel(self.root, bg="#0a0a1a")
        win.title("File Manager")
        win.geometry("500x400")
        tk.Label(win, text="📁 Luo OS File Manager", fg="#00ffcc", bg="#0a0a1a", font=("Courier", 14, "bold")).pack(pady=10)
        files = os.listdir(os.path.expanduser("~"))
        for f in files[:20]:
            tk.Label(win, text=f"  {f}", fg="#ffffff", bg="#0a0a1a", font=("Courier", 11)).pack(anchor="w", padx=20)

    def open_settings(self):
        win = tk.Toplevel(self.root, bg="#0a0a1a")
        win.title("Settings")
        win.geometry("400x300")
        tk.Label(win, text="⚙️ Luo OS Settings", fg="#00ffcc", bg="#0a0a1a", font=("Courier", 14, "bold")).pack(pady=10)
        settings = ["Theme: Dark", "AI Core: Enabled", "Compat Layer: Wine", "Shell: Bash + PowerShell"]
        for s in settings:
            tk.Label(win, text=f"  • {s}", fg="#ffffff", bg="#0a0a1a", font=("Courier", 11)).pack(anchor="w", padx=20)

    def open_start_menu(self):
        win = tk.Toplevel(self.root, bg="#111133")
        win.title("Start")
        win.geometry("200x300")
        win.overrideredirect(True)
        win.place_window_center()
        items = ["🖥️ Terminal", "🤖 Luo AI", "📁 Files", "⚙️ Settings", "❌ Shutdown"]
        for item in items:
            tk.Button(win, text=item, font=("Courier", 12), bg="#111133", fg="#00ffcc", relief="flat", width=20).pack(pady=5)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    desktop = LuoDesktop()
    desktop.run()
