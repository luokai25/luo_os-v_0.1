import os, subprocess, json, shutil, urllib.request, urllib.parse, re
from pathlib import Path
from datetime import datetime

TOOLS = {}

def tool(name, desc, perm=False):
    def dec(fn):
        TOOLS[name] = {"fn":fn,"description":desc,"requires_permission":perm}
        return fn
    return dec

@tool("read_file","Read a file")
def read_file(path):
    try:
        p=Path(path).expanduser()
        if not p.exists(): return f"[ERROR] Not found: {path}"
        if p.stat().st_size>1_000_000: return "[ERROR] File too large"
        return p.read_text(errors="replace")
    except Exception as e: return f"[ERROR] {e}"

@tool("write_file","Write content to a file",perm=True)
def write_file(path,content):
    try:
        p=Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content); return f"Written {len(content)} chars to {path}"
    except Exception as e: return f"[ERROR] {e}"

@tool("append_file","Append to a file",perm=True)
def append_file(path,content):
    try:
        with open(Path(path).expanduser(),"a") as f: f.write(content)
        return f"Appended to {path}"
    except Exception as e: return f"[ERROR] {e}"

@tool("list_dir","List directory contents")
def list_dir(path="."):
    try:
        p=Path(path).expanduser()
        if not p.exists(): return f"[ERROR] Not found: {path}"
        return "\n".join(f"[{'DIR' if i.is_dir() else 'FILE'}] {i.name}" for i in sorted(p.iterdir())) or "(empty)"
    except Exception as e: return f"[ERROR] {e}"

@tool("delete_file","Delete a file",perm=True)
def delete_file(path):
    try:
        p=Path(path).expanduser()
        if not p.exists(): return f"[ERROR] Not found"
        p.unlink(); return f"Deleted: {path}"
    except Exception as e: return f"[ERROR] {e}"

@tool("file_exists","Check if file exists")
def file_exists(path):
    p=Path(path).expanduser()
    return f"EXISTS: {path}" if p.exists() else f"NOT FOUND: {path}"

@tool("bash","Run a shell command",perm=True)
def bash(command,timeout=30):
    try:
        r=subprocess.run(command,shell=True,capture_output=True,text=True,timeout=timeout)
        parts=[]
        if r.stdout.strip(): parts.append(f"STDOUT:\n{r.stdout.strip()}")
        if r.stderr.strip(): parts.append(f"STDERR:\n{r.stderr.strip()}")
        if r.returncode!=0: parts.append(f"EXIT: {r.returncode}")
        return "\n".join(parts) or "(no output)"
    except subprocess.TimeoutExpired: return f"[ERROR] Timeout after {timeout}s"
    except Exception as e: return f"[ERROR] {e}"

@tool("web_search","Search the web via DuckDuckGo")
def web_search(query,max_results=5):
    try:
        url=f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r: html=r.read().decode("utf-8",errors="replace")
        clean=lambda s: re.sub(r"<[^>]+>","",s).strip()
        titles=re.findall(r'class="result__a"[^>]*>(.*?)</a>',html,re.DOTALL)
        snips=re.findall(r'class="result__snippet"[^>]*>(.*?)</a>',html,re.DOTALL)
        out=[f"{i+1}. {clean(t)}\n   {clean(s)}" for i,(t,s) in enumerate(zip(titles[:max_results],snips[:max_results]))]
        return "\n\n".join(out) or "No results."
    except Exception as e: return f"[ERROR] {e}"

@tool("run_python","Execute Python code",perm=True)
def run_python(code,timeout=15):
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode="w",suffix=".py",delete=False) as f:
            f.write(code); tmp=f.name
        r=subprocess.run(["python3",tmp],capture_output=True,text=True,timeout=timeout)
        os.unlink(tmp)
        parts=[]
        if r.stdout.strip(): parts.append(f"OUTPUT:\n{r.stdout.strip()}")
        if r.stderr.strip(): parts.append(f"ERRORS:\n{r.stderr.strip()}")
        return "\n".join(parts) or "(no output)"
    except subprocess.TimeoutExpired: return f"[ERROR] Timeout"
    except Exception as e: return f"[ERROR] {e}"

@tool("get_datetime","Get current date and time")
def get_datetime(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool("system_info","Get system information")
def system_info(): return bash("uname -a && free -h && df -h /")

class ToolExecutor:
    def __init__(self, auto_approve=False): self.auto_approve=auto_approve

    def execute(self, name, args, ask_permission=None):
        if name not in TOOLS: return f"[ERROR] Unknown tool: {name}"
        t=TOOLS[name]
        if t["requires_permission"] and not self.auto_approve:
            if ask_permission:
                if not ask_permission(name,args): return "[DENIED]"
            else: return f"[SKIPPED] {name} needs permission"
        try: return t["fn"](**args)
        except Exception as e: return f"[ERROR] {e}"

    def list_tools(self):
        return "\n".join(f"  {n}{' [perm]' if t['requires_permission'] else ''} — {t['description']}" for n,t in TOOLS.items())
