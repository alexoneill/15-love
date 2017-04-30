#!/usr/bin/python2
# current_bridge.py
# nroberts, 4/29/2017
# bridge is PauschBridge if -p flag is specified; TerminalBridge if -v is specified,
# otherwise, silent bridge

from bridge import Bridge

import sys

# silent
if "-v" in sys.argv:
    from terminal_bridge import TerminalBridge
else:
    class TerminalBridge(Bridge):
        def init(self): pass
        def paint(self): pass

# Only import actual bridge if we're running on the bridge
if "-p" in sys.argv:
    from pausch_bridge import PauschBridge

bridge = PauschBridge if "-p" in sys.argv else TerminalBridge
