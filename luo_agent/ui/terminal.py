import sys, os, readline
from datetime import datetime
from pathlib import Path
from core.config import LuoConfig
from memory.memory import MemorySystem
from agents.agent import LuoAgentCore
from core.llm import OllamaClient

R="\033[0m";B="\033[1m";DIM="\033[2m";CY="\033[96m";GR="\033[92m";YL="\033[93m";RD="\033[91m";MG="\033[95m"

BANNER=f"""{CY}{B}
 ██╗     ██╗   ██╗ ██████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗
 ██║     ██║   ██║██╔═══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
 ██║     ██║   ██║██║   ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
 ██║     ██║   ██║██║   ██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
 ███████╗╚██████╔╝╚██████╔╝    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
 ╚══════╝ ╚═════╝  ╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
{R}{DIM} Autonomous AI Agent — Luo OS | Powered by Ollama (free, local, offline){R}
"""

HELP=f"""
{B}Commands:{R}
  {CY}/model <n>{R}   switch model     {CY}/models{R}     list models
  {CY}/memory{R}      show memory      {CY}/dream{R}      run autoDream
  {CY}/notes{R}       list notes       {CY}/status{R}     agent status
  {CY}/save{R}        save session     {CY}/load <id>{R}  load session
  {CY}/clear{R}       clear context    {CY}/exit{R}       quit
"""

class LuoTerminal:
    def __init__(self, config):
        self.config=config
        self.memory=MemorySystem(config.memory_file,config.notes_dir,config.sessions_dir)
        self.llm=OllamaClient(config.ollama_url,config.model)
        self.agent=LuoAgentCore(config,self.memory)
        self.sid=datetime.now().strftime("session_%Y%m%d_%H%M%S")
        try:
            h=Path("~/.luo_agent/.history").expanduser()
            h.parent.mkdir(parents=True,exist_ok=True)
            if h.exists(): readline.read_history_file(str(h))
            readline.set_history_length(500)
            import atexit; atexit.register(readline.write_history_file,str(h))
        except: pass

    def p(self,t,c=R,end="\n"): print(f"{c}{t}{R}",end=end); sys.stdout.flush()

    def _cmd(self, cmd):
        parts=cmd.strip().split(None,1); c=parts[0].lower(); arg=parts[1] if len(parts)>1 else ""
        if c=="/help": print(HELP)
        elif c=="/model":
            if not arg: self.p(f"Current: {self.config.model}",CY)
            else:
                self.config.set("model",arg); self.llm.model=self.agent.llm.model=arg
                self.p(f"✓ Model → {arg}",GR)
        elif c=="/models":
            ms=self.llm.list_models()
            if ms: self.p("Models:",CY); [self.p(f"  {m}{' ←' if m==self.config.model else ''}",GR if m==self.config.model else R) for m in ms]
            else: self.p("None found. Run: ollama pull tinyllama",YL)
        elif c=="/memory": self.p("── Memory ──",CY); print(self.memory.read_memory())
        elif c=="/notes":
            ns=self.memory.list_notes()
            if ns: self.p("── Notes ──",CY); [self.p(f"  {n}",DIM) for n in ns]
            else: self.p("No notes yet.",DIM)
        elif c=="/sessions":
            ss=self.memory.list_sessions()
            if ss: self.p("── Sessions ──",CY); [self.p(f"  {s}",DIM) for s in ss[:10]]
            else: self.p("No sessions yet.",DIM)
        elif c=="/load":
            if not arg: self.p("Usage: /load <id>",YL)
            else: self.agent.load_conversation(arg); self.p(f"✓ Loaded: {arg}",GR)
        elif c=="/save": self.agent.save_conversation(self.sid); self.p(f"✓ Saved: {self.sid}",GR)
        elif c=="/clear": self.agent.reset_conversation(); self.p("✓ Cleared.",GR)
        elif c=="/dream":
            if self.llm.is_available(): self.p(self.memory.auto_dream(self.llm),GR)
            else: self.p("Ollama offline.",RD)
        elif c=="/status":
            ok=self.llm.is_available()
            self.p("── Status ──",CY)
            self.p(f"  Model   : {self.config.model}",B)
            self.p(f"  Ollama  : {'✓ online' if ok else '✗ offline'}",GR if ok else RD)
            self.p(f"  Session : {self.sid}",DIM)
            self.p(f"  Messages: {len(self.agent.conversation)}",DIM)
        elif c in ("/exit","/quit","/q"):
            self.agent.save_conversation(self.sid); self.p("Goodbye.",DIM); sys.exit(0)
        else: return False
        return True

    def run(self):
        os.system("clear")
        print(BANNER)
        if self.llm.is_available(): self.p(f"✓ Ollama online — {self.config.model}",GR)
        else: self.p("⚠  Ollama offline. Run: ollama serve",YL)
        self.p("\nType a message or /help\n",DIM)
        while True:
            try: user=input(f"{CY}{B}you{R}{CY} ▸ {R}").strip()
            except (KeyboardInterrupt,EOFError):
                self.agent.save_conversation(self.sid); self.p("\nGoodbye.",DIM); break
            if not user: continue
            if user.startswith("/"): self._cmd(user); continue
            if not self.llm.is_available(): self.p("✗ Ollama offline.",RD); continue
            print(f"\n{MG}{B}luo{R}{MG} ▸ {R}",end="")
            try:
                self.agent.chat(user,stream_callback=lambda t:print(f"{MG}{t}{R}",end="",flush=True))
                print("\n")
            except Exception as e: self.p(f"\n[ERROR] {e}",RD)
