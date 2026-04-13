#!/usr/bin/env python3
"""
LuoOS — Single-click launcher (Mac / Linux / Windows)
Installs the 2 required packages then starts LuoOS.
"""
import os, sys, subprocess, time, argparse, socket, threading, webbrowser
from pathlib import Path

PORT   = 3000
ROOT   = Path(__file__).parent.resolve()
SERVER = ROOT / "luo_server.py"
PKGS   = ["flask", "flask-cors"]

BANNER = """
  ██╗     ██╗   ██╗ ██████╗      ██████╗ ███████╗
  ██║     ██║   ██║██╔═══██╗    ██╔═══██╗██╔════╝
  ██║     ██║   ██║██║   ██║    ██║   ██║███████╗
  ██║     ██║   ██║██║   ██║    ██║   ██║╚════██║
  ███████╗╚██████╔╝╚██████╔╝    ╚██████╔╝███████║
  ╚══════╝ ╚═════╝  ╚═════╝      ╚═════╝ ╚══════╝
           The AI-Native OS  —  by Luo Kai
"""

G="\033[92m"; Y="\033[93m"; R="\033[91m"; C="\033[96m"; X="\033[0m"
ok   = lambda t: print(f"{G}  ✅  {t}{X}")
warn = lambda t: print(f"{Y}  ⚠️   {t}{X}")
err  = lambda t: print(f"{R}  ❌  {t}{X}")
info = lambda t: print(f"{C}  →   {t}{X}")

def check_python():
    if sys.version_info < (3, 8):
        err(f"Python 3.8+ needed. You have {sys.version}")
        sys.exit(1)
    ok(f"Python {sys.version.split()[0]}")

def install_pkgs():
    missing = []
    for p in PKGS:
        try: __import__(p.replace("-","_"))
        except ImportError: missing.append(p)
    if not missing:
        ok("flask + flask-cors ready"); return
    print(f"\n  Installing: {', '.join(missing)} (one-time, ~10 sec)\n")
    for flags in ([],[" --user"]):
        try:
            subprocess.check_call(
                [sys.executable,"-m","pip","install","--quiet"]+flags+missing,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            ok(f"Installed: {', '.join(missing)}"); return
        except: pass
    err("pip install failed. Run: pip install flask flask-cors"); sys.exit(1)

def port_free(p):
    with socket.socket() as s: return s.connect_ex(("127.0.0.1",p)) != 0

def open_browser(url, delay=1.5):
    def _go():
        time.sleep(delay); webbrowser.open(url)
    threading.Thread(target=_go, daemon=True).start()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port",  type=int, default=PORT)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-install", action="store_true")
    args = ap.parse_args()

    print(f"{C}{BANNER}{X}")
    check_python()
    if not args.no_install: install_pkgs()

    port = args.port
    if not port_free(port):
        warn(f"Port {port} busy — trying {port+1}"); port += 1
        if not port_free(port): err(f"Port {port} also busy. Use --port N"); sys.exit(1)

    url = f"http://localhost:{port}"
    print(f"\n  {'─'*52}")
    info(f"LuoOS starting → {G}{url}{X}")
    info(f"LUOKAI brain: independent — no external model")
    info(f"Skills loaded: 4,146 across 20 domains")
    print(f"  {'─'*52}")
    print(f"\n  Ctrl+C to stop\n")

    if not args.quiet: open_browser(url)

    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    os.environ["LUO_PORT"] = str(port)

    try:
        exec(compile(open(SERVER).read(), str(SERVER), "exec"),
             {"__name__": "__main__", "__file__": str(SERVER)})
    except KeyboardInterrupt:
        print(f"\n\n  {Y}LuoOS stopped.{X} Goodbye.\n")
        sys.exit(0)

if __name__ == "__main__": main()
