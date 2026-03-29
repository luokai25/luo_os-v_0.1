#!/usr/bin/env python3
"""
Luo OS Package Manager — luo install <app>
Free app installer for Luo OS
Created by Luo Kai (luokai25)
"""

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime

PKG_DIR = os.path.expanduser("~/.luo_packages")
PKG_DB = os.path.join(PKG_DIR, "installed.json")

# Built-in package registry
REGISTRY = {
    "vim": {
        "description": "Text editor",
        "install": "apt-get install -y vim",
        "category": "editor"
    },
    "git": {
        "description": "Version control",
        "install": "apt-get install -y git",
        "category": "dev"
    },
    "python3": {
        "description": "Python programming language",
        "install": "apt-get install -y python3 python3-pip",
        "category": "dev"
    },
    "rust": {
        "description": "Rust programming language",
        "install": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        "category": "dev"
    },
    "nodejs": {
        "description": "JavaScript runtime",
        "install": "apt-get install -y nodejs npm",
        "category": "dev"
    },
    "wine": {
        "description": "Windows compatibility layer",
        "install": "apt-get install -y wine",
        "category": "compat"
    },
    "vlc": {
        "description": "Media player",
        "install": "apt-get install -y vlc",
        "category": "media"
    },
    "firefox": {
        "description": "Web browser",
        "install": "apt-get install -y firefox",
        "category": "browser"
    },
    "ollama": {
        "description": "Local AI model runner",
        "install": "curl -fsSL https://ollama.com/install.sh | sh",
        "category": "ai"
    },
    "tinyllama": {
        "description": "TinyLlama local AI model",
        "install": "ollama pull tinyllama",
        "category": "ai"
    },
    "mistral": {
        "description": "Mistral 7B local AI model",
        "install": "ollama pull mistral",
        "category": "ai"
    },
    "htop": {
        "description": "System monitor",
        "install": "apt-get install -y htop",
        "category": "system"
    },
    "neofetch": {
        "description": "System info display",
        "install": "apt-get install -y neofetch",
        "category": "system"
    },
    "ffmpeg": {
        "description": "Media converter",
        "install": "apt-get install -y ffmpeg",
        "category": "media"
    },
    "docker": {
        "description": "Container runtime",
        "install": "apt-get install -y docker.io",
        "category": "dev"
    }
}

def load_db():
    os.makedirs(PKG_DIR, exist_ok=True)
    if os.path.exists(PKG_DB):
        with open(PKG_DB) as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(PKG_DB, "w") as f:
        json.dump(db, f, indent=2)

def cmd_install(pkg_name):
    if pkg_name not in REGISTRY:
        print(f"❌ Package '{pkg_name}' not found.")
        print(f"   Run: luo search {pkg_name}")
        return
    pkg = REGISTRY[pkg_name]
    print(f"Installing {pkg_name} — {pkg['description']}...")
    result = subprocess.run(pkg["install"], shell=True)
    if result.returncode == 0:
        db = load_db()
        db[pkg_name] = {"installed": datetime.now().isoformat(), "version": "latest"}
        save_db(db)
        print(f"✅ {pkg_name} installed successfully!")
    else:
        print(f"❌ Failed to install {pkg_name}")

def cmd_remove(pkg_name):
    db = load_db()
    if pkg_name not in db:
        print(f"❌ {pkg_name} is not installed")
        return
    result = subprocess.run(f"apt-get remove -y {pkg_name}", shell=True)
    if result.returncode == 0:
        del db[pkg_name]
        save_db(db)
        print(f"✅ {pkg_name} removed")

def cmd_list():
    db = load_db()
    if not db:
        print("No packages installed via luo pkg yet.")
        return
    print(f"{'Package':<20} {'Installed':<25}")
    print("-" * 45)
    for name, info in db.items():
        print(f"{name:<20} {info['installed']:<25}")

def cmd_search(query):
    results = [(k, v) for k, v in REGISTRY.items() if query.lower() in k.lower() or query.lower() in v["description"].lower()]
    if not results:
        print(f"No packages found for: {query}")
        return
    print(f"{'Package':<20} {'Category':<12} {'Description'}")
    print("-" * 60)
    for name, info in results:
        print(f"{name:<20} {info['category']:<12} {info['description']}")

def cmd_available():
    print(f"{'Package':<20} {'Category':<12} {'Description'}")
    print("-" * 60)
    for name, info in sorted(REGISTRY.items(), key=lambda x: x[1]["category"]):
        print(f"{name:<20} {info['category']:<12} {info['description']}")

def cmd_update():
    print("Updating Luo OS package database...")
    subprocess.run("apt-get update -y", shell=True)
    print("✅ Updated")

def usage():
    print("""
╔══════════════════════════════════════════╗
║   Luo OS Package Manager                ║
║   Free software for everyone            ║
╚══════════════════════════════════════════╝

Usage:
  python3 luo_pkg.py install <package>   — Install a package
  python3 luo_pkg.py remove  <package>   — Remove a package
  python3 luo_pkg.py list                — List installed packages
  python3 luo_pkg.py search  <query>     — Search packages
  python3 luo_pkg.py available           — Show all packages
  python3 luo_pkg.py update              — Update package database

Categories: ai, dev, editor, browser, media, system, compat
""")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        usage()
    elif args[0] == "install" and len(args) > 1:
        cmd_install(args[1])
    elif args[0] == "remove" and len(args) > 1:
        cmd_remove(args[1])
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "search" and len(args) > 1:
        cmd_search(args[1])
    elif args[0] == "available":
        cmd_available()
    elif args[0] == "update":
        cmd_update()
    else:
        usage()
