#!/usr/bin/env python3
"""Luo OS Package Manager v0.2"""
import json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

PKG_DIR = Path("~/.luo_packages").expanduser()
PKG_DB  = PKG_DIR / "installed.json"
GR="[92m"; RD="[91m"; YL="[93m"; CY="[96m"; B="[1m"; R="[0m"; DIM="[2m"

REGISTRY = {
    "tinyllama":    {"desc":"TinyLlama 1.1B — 1GB RAM",         "cmd":"ollama pull tinyllama",                     "cat":"ai",     "size":"~600MB"},
    "qwen2.5:1.5b": {"desc":"Qwen 2.5 1.5B — better reasoning","cmd":"ollama pull qwen2.5:1.5b",                   "cat":"ai",     "size":"~1GB"},
    "phi3:mini":    {"desc":"Phi-3 Mini — best coding (4GB+)",  "cmd":"ollama pull phi3:mini",                     "cat":"ai",     "size":"~2.3GB"},
    "gemma2:2b":    {"desc":"Gemma 2B — general (3GB+)",        "cmd":"ollama pull gemma2:2b",                     "cat":"ai",     "size":"~1.6GB"},
    "mistral":      {"desc":"Mistral 7B — advanced (8GB+)",     "cmd":"ollama pull mistral",                       "cat":"ai",     "size":"~4GB"},
    "ollama":       {"desc":"Local AI model runner",            "cmd":"curl -fsSL https://ollama.com/install.sh|sh","cat":"ai",     "size":"~50MB"},
    "git":          {"desc":"Version control",                  "cmd":"apt-get install -y git",                    "cat":"dev",    "size":"~30MB"},
    "python3":      {"desc":"Python 3 + pip",                   "cmd":"apt-get install -y python3 python3-pip",    "cat":"dev",    "size":"~50MB"},
    "nodejs":       {"desc":"Node.js + npm",                    "cmd":"apt-get install -y nodejs npm",             "cat":"dev",    "size":"~70MB"},
    "rust":         {"desc":"Rust language",                    "cmd":"curl --proto=https --tlsv1.2 -sSf https://sh.rustup.rs|sh -s -- -y","cat":"dev","size":"~200MB"},
    "gcc":          {"desc":"C/C++ compiler",                   "cmd":"apt-get install -y gcc g++",                "cat":"dev",    "size":"~30MB"},
    "docker":       {"desc":"Container runtime",                "cmd":"apt-get install -y docker.io",              "cat":"dev",    "size":"~100MB"},
    "vim":          {"desc":"Terminal text editor",             "cmd":"apt-get install -y vim",                    "cat":"editor", "size":"~3MB"},
    "nano":         {"desc":"Simple editor",                    "cmd":"apt-get install -y nano",                   "cat":"editor", "size":"~1MB"},
    "htop":         {"desc":"Process viewer",                   "cmd":"apt-get install -y htop",                   "cat":"system", "size":"~200KB"},
    "neofetch":     {"desc":"System info",                      "cmd":"apt-get install -y neofetch",               "cat":"system", "size":"~500KB"},
    "tmux":         {"desc":"Terminal multiplexer",             "cmd":"apt-get install -y tmux",                   "cat":"system", "size":"~500KB"},
    "tree":         {"desc":"Directory tree viewer",            "cmd":"apt-get install -y tree",                   "cat":"system", "size":"~100KB"},
    "wget":         {"desc":"File downloader",                  "cmd":"apt-get install -y wget",                   "cat":"system", "size":"~2MB"},
    "ffmpeg":       {"desc":"Media converter",                  "cmd":"apt-get install -y ffmpeg",                 "cat":"media",  "size":"~60MB"},
    "vlc":          {"desc":"Media player",                     "cmd":"apt-get install -y vlc",                    "cat":"media",  "size":"~50MB"},
    "firefox":      {"desc":"Firefox browser",                  "cmd":"apt-get install -y firefox",                "cat":"browser","size":"~70MB"},
    "wine":         {"desc":"Windows app compat",               "cmd":"apt-get install -y wine",                   "cat":"compat", "size":"~300MB"},
    "pip-requests": {"desc":"Python requests",                  "cmd":"pip3 install requests --break-system-packages","cat":"python","size":"~100KB"},
    "pip-flask":    {"desc":"Flask web framework",              "cmd":"pip3 install flask --break-system-packages", "cat":"python","size":"~2MB"},
    "pip-numpy":    {"desc":"NumPy",                            "cmd":"pip3 install numpy --break-system-packages", "cat":"python","size":"~20MB"},
}

def load_db():
    PKG_DIR.mkdir(parents=True, exist_ok=True)
    try: return json.loads(PKG_DB.read_text()) if PKG_DB.exists() else {}
    except: return {}

def save_db(db): PKG_DB.write_text(json.dumps(db, indent=2))

def cmd_install(name):
    if name not in REGISTRY: print(f"{RD}Not found: {name}{R}"); return
    pkg = REGISTRY[name]
    print(f"{YL}Installing {B}{name}{R}{YL} — {pkg['desc']} ({pkg['size']}){R}")
    r = subprocess.run(pkg["cmd"], shell=True)
    if r.returncode == 0:
        db = load_db(); db[name] = {"installed": datetime.now().isoformat(), "category": pkg["cat"]}
        save_db(db); print(f"{GR}{B}✓ {name} installed{R}")
    else: print(f"{RD}✗ Failed{R}")

def cmd_remove(name):
    db = load_db()
    if name not in db: print(f"{RD}Not installed: {name}{R}"); return
    subprocess.run(f"apt-get remove -y {name}", shell=True)
    del db[name]; save_db(db); print(f"{GR}✓ {name} removed{R}")

def cmd_list():
    db = load_db()
    if not db: print("Nothing installed yet."); return
    print(f"
{B}Installed ({len(db)}):{R}")
    for n, info in sorted(db.items()):
        print(f"  {GR}{n:<22}{R} {DIM}{info.get('category','?'):<10}{R} {info['installed'][:10]}")

def cmd_search(q):
    results = [(k,v) for k,v in REGISTRY.items() if q.lower() in k.lower() or q.lower() in v["desc"].lower()]
    if not results: print(f"Nothing found for: {q}"); return
    print(f"
{B}Results for '{q}':{R}")
    for n, p in results: print(f"  {CY}{n:<22}{R} {DIM}{p['cat']:<10}{R} {p['size']:<10} {p['desc']}")

def cmd_available(cat=""):
    db = load_db()
    pkgs = [(k,v) for k,v in REGISTRY.items() if not cat or v["cat"]==cat]
    if not pkgs: print(f"No packages in: {cat}"); return
    print(f"
{B}Available ({len(pkgs)}):{R}")
    cur = ""
    for n, p in sorted(pkgs, key=lambda x:(x[1]["cat"],x[0])):
        if p["cat"] != cur: cur = p["cat"]; print(f"
  {B}{CY}[{cur.upper()}]{R}")
        mark = f"{GR} ✓{R}" if n in db else ""
        print(f"    {n:<22} {DIM}{p['size']:<10}{R} {p['desc']}{mark}")

def usage():
    print(f"""
{B}Luo OS Package Manager v0.2{R}
  install <pkg>       install
  remove  <pkg>       remove
  list                installed packages
  search  <query>     search
  available [cat]     browse all (cats: ai dev editor system media browser compat python)
""")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:                                   usage()
    elif a[0]=="install" and len(a)>1:         cmd_install(a[1])
    elif a[0]=="remove"  and len(a)>1:         cmd_remove(a[1])
    elif a[0]=="list":                          cmd_list()
    elif a[0]=="search"  and len(a)>1:         cmd_search(a[1])
    elif a[0]=="available":                     cmd_available(a[1] if len(a)>1 else "")
    else:                                       usage()
