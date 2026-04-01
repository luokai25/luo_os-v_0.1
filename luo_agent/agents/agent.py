import json, re
from typing import Optional, Callable
from core.llm import OllamaClient
from core.config import LuoConfig
from memory.memory import MemorySystem
from tools.tools import ToolExecutor

SYS = """You are Luo, an autonomous AI agent inside Luo OS.
To use a tool respond with:
```tool
{{"tool":"name","args":{{"key":"value"}}}}
```
Tools:
{tools}
Memory:
{memory}
Be concise. Use tools when needed. Confirm destructive actions."""

class LuoAgentCore:
    def __init__(self, config, memory):
        self.config=config; self.memory=memory
        self.llm=OllamaClient(config.ollama_url,config.model)
        self.tools=ToolExecutor(); self.conversation=[]

    def _sys(self):
        return SYS.format(tools=self.tools.list_tools(),memory=self.memory.get_context_summary())

    def _extract_tool(self, text):
        m=re.search(r"```tool\s*(\{.*?\})\s*```",text,re.DOTALL)
        if m:
            try: return json.loads(m.group(1))
            except: pass
        return None

    def _perm(self, name, args):
        print(f"\n⚠  Luo wants: {name} | args: {args}")
        return input("Allow? [y/N]: ").strip().lower() in ("y","yes")

    def chat(self, user_input, stream_callback=None):
        self.conversation.append({"role":"user","content":user_input})
        messages=[{"role":"system","content":self._sys()}]+self.conversation
        final=""; loops=0
        while loops<8:
            if stream_callback:
                resp=""
                for tok in self.llm.stream_chat(messages,temperature=self.config.get("temperature",0.7)):
                    resp+=tok; stream_callback(tok)
            else:
                resp=self.llm.chat(messages,temperature=self.config.get("temperature",0.7))
            if not resp or resp.startswith("[ERROR]"): final=resp or "[ERROR]"; break
            call=self._extract_tool(resp)
            if call:
                name=call.get("tool",""); args=call.get("args",{})
                result=self.tools.execute(name,args,ask_permission=self._perm)
                self.conversation.append({"role":"assistant","content":resp})
                self.conversation.append({"role":"user","content":f"[Tool:{name}]\n{result}"})
                messages=[{"role":"system","content":self._sys()}]+self.conversation
                if stream_callback: stream_callback(f"\n[🔧{name}]→{result[:150]}\n")
                loops+=1; continue
            final=resp; break
        self.conversation.append({"role":"assistant","content":final})
        if len(final)>80: self.memory.append_memory(f"Topic:{user_input[:50]}")
        return final

    def reset_conversation(self): self.conversation=[]
    def save_conversation(self,sid): self.memory.save_session(sid,self.conversation)
    def load_conversation(self,sid): self.conversation=self.memory.load_session(sid)
