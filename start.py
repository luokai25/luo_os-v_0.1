#!/usr/bin/env python3
"""
LuoOS — Single Click Start
Windows: double-click start.bat  |  Mac/Linux: ./start.sh
Everything starts automatically. No steps. No config. No Ollama.
"""
import os, sys, subprocess, time, socket, threading, webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
PORT = 3000

BANNER = """
  ██╗     ██╗   ██╗ ██████╗      ██████╗ ███████╗
  ██║     ██║   ██║██╔═══██╗    ██╔═══██╗██╔════╝
  ██║     ██║   ██║██║   ██║    ██║   ██║███████╗
  ██║     ██║   ██║██║   ██║    ██║   ██║╚════██║
  ███████╗╚██████╔╝╚██████╔╝    ╚██████╔╝███████║
  ╚══════╝ ╚═════╝  ╚═════╝      ╚═════╝ ╚══════╝
  The AI-Native OS  —  by Luo Kai   (v1.0)
"""

C="\033[96m"; G="\033[92m"; Y="\033[93m"; R="\033[0m"
step = lambda m: print(f"{G}  ✅  {m}{R}")
warn = lambda m: print(f"{Y}  ⚠️   {m}{R}")
info = lambda m: print(f"{C}  →   {m}{R}")

# 1. Python check
if sys.version_info < (3, 6):
    print("\n  LuoOS needs Python 3.6+. Have " + str(sys.version_info.major) + "." + str(sys.version_info.minor))
    print("      https://python.org/downloads\n")
    input("Press Enter to exit..."); sys.exit(1)

print(f"{C}{BANNER}{R}")
step(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# 2. Auto-install flask
import importlib.util
missing = [pip for mod,pip in [("flask","flask"),("flask_cors","flask-cors")]
           if not importlib.util.find_spec(mod)]
if missing:
    print(f"\n  Installing: {', '.join(missing)}  (one-time, ~10s)\n")
    try:
        subprocess.check_call([sys.executable,"-m","pip","install","--quiet"]+missing,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        step(f"Installed: {', '.join(missing)}")
    except:
        warn(f"Run: pip install {' '.join(missing)}")
        input("Press Enter to exit..."); sys.exit(1)
else:
    step("Dependencies ready")

# 3. Port
def port_free(p):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1",p)) != 0

if not port_free(PORT):
    PORT += 1
    warn(f"Port 3000 busy — using {PORT}")

os.environ["LUO_PORT"] = str(PORT)
url = f"http://localhost:{PORT}"

# 4. Browser opener — waits for server to be ready
def open_browser():
    for _ in range(40):
        time.sleep(0.5)
        if not port_free(PORT):
            time.sleep(0.8)
            webbrowser.open(url)
            return
    webbrowser.open(url)

threading.Thread(target=open_browser, daemon=True).start()

# 5. Start
print(f"\n  {'─'*54}")
info(f"Starting LuoOS  →  {G}{url}{R}")
info("LUOKAI: independent brain — 4,146 skills loaded")
info("Press Ctrl+C to stop")
print(f"  {'─'*54}\n")

try:
    # Check if model weights are present, inform user if downloading
    try:
        from luokai.core.model_engine import MODELS_DIR, PRIMARY_MODEL
        model_path = MODELS_DIR / PRIMARY_MODEL["filename"]
        if not model_path.exists():
            info(f"First run detected — LUOKAI will download AI weights (~{PRIMARY_MODEL['size_gb']:.1f}GB)")
            info("This happens once. After that LUOKAI runs fully offline.")
            info(f"Saving to: {MODELS_DIR}")
        else:
            step(f"AI weights found: {model_path.name} ({model_path.stat().st_size/1e9:.1f}GB)")
    except Exception:
        pass

    import luo_server
    luo_server._run_server()
except KeyboardInterrupt:
    print(f"\n\n  {Y}LuoOS stopped.{R}  See you next time.\n")
    sys.exit(0)
except Exception as e:
    print(f"\n  ❌  {e}\n  Try: python3 luo_server.py")
    input("\nPress Enter to exit..."); sys.exit(1)
