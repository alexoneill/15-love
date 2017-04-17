#!/usr/bin/python2
# test.py
# nroberts 04/10/2017
# Instead of lighting up a bridge, we light up the terminal

from tennis_show import TennisShow
from terminal_bridge import TerminalBridge

import sys

# Only import actual bridge if we're running on the bridge
if sys.argv[0] == "-p":
    from pausch_bridge import PauschBridge

from threading import Thread
import Queue

thread_continuing = True

def main(bridge):
    global thread_continuing
    print "Usage: Press 1 for player 1 swing, 2 for player 2 swing (followed by Enter)"
    print "To quit, press Ctrl+C and then Enter"
    inqueue = Queue.Queue()
    outqueue = Queue.Queue()
    show = TennisShow(bridge(), inqueue=inqueue, outqueue=outqueue)

    def cause_problems():
        global thread_continuing
        while thread_continuing:
            try:
                x = int(raw_input())
                inqueue.put(("swing", { "player": x }))
            except:
                # error reading int
                pass

    # put something new on the inqueue every 10 seconds
    thread = Thread(target = cause_problems)
    thread.start()

    # run the show
    try:
        show.run(framerate=40)
    finally:
        thread_continuing = False

if __name__ == "__main__":
    bridge = PauschBridge if sys.argv[0] == "-p" else TerminalBridge
    main(bridge)
