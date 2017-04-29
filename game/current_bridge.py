#!/usr/bin/python2
# current_bridge.py
# nroberts, 4/29/2017
# bridge is PauschBridge if -p flag is specified; silent bridge if -s is specified,
# and TerminalBridge if no options are specified.

from bridge import Bridge

import sys

# silent
if "-s" in sys.argv:
    class TerminalBridge(Bridge):
        def init(self): pass
        def paint(self): pass
else:
    from terminal_bridge import TerminalBridge

# Only import actual bridge if we're running on the bridge
if "-p" in sys.argv:
    from pausch_bridge import PauschBridge

bridge = PauschBridge if "-p" in sys.argv else TerminalBridge
