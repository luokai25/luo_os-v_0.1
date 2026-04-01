#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from core.daemon import LuoDaemon
from core.config import LuoConfig
from ui.terminal import LuoTerminal

def main():
    config = LuoConfig()
    if "--daemon" in sys.argv:
        LuoDaemon(config).start()
    else:
        LuoTerminal(config).run()

if __name__ == "__main__":
    main()
