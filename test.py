#!/usr/bin/python2
# test.py
# nroberts 04/10/2017
# Instead of lighting up a bridge, we light up the terminal

from tennis_show import TennisShow
from bridge import Bridge
import threading
import Queue

class TerminalBridge(Bridge):
    def init(self):
        print "Initializing terminal bridge..."

    def paint(self):
        print "Painting bridge"
        # Print informative message to the terminal
        for light in self.lights:
            print light

def main():
    inqueue = Queue.Queue()
    outqueue = Queue.Queue()
    show = TennisShow(TerminalBridge(), inqueue=inqueue, outqueue=outqueue)

    def cause_problems():
        inqueue.put(("swing", { "player": 1 }))
        threading.Timer(10, cause_problems).start()

    # put something new on the inqueue every 10 seconds
    cause_problems()

    # run the show
    show.run(framerate=2)

if __name__ == "__main__":
    main()
