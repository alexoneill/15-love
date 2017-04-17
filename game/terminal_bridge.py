#!/usr/bin/python2
# terminal_bridge.py
# nroberts 04/16/2017
# Test bridge for printing to terminal

from bridge import Bridge

class TerminalBridge(Bridge):
    def init(self):
        print "Initializing terminal bridge..."

    def paint(self):
        # Print informative message to the terminal
        for light in self.lights():
            print light

