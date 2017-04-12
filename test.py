#!/usr/bin/python2
# test.py
# nroberts 04/10/2017
# Instead of lighting up a bridge, we light up the terminal

from tennis_show import TennisShow
from bridge import Bridge
from threading import Thread
import Queue

class TerminalBridge(Bridge):
    def init(self):
        print "Initializing terminal bridge..."

    def paint(self):
        print "Painting bridge"
        # Print informative message to the terminal
        for light in self.lights:
            print light

thread_continuing = True

def main():
    inqueue = Queue.Queue()
    outqueue = Queue.Queue()
    show = TennisShow(TerminalBridge(), inqueue=inqueue, outqueue=outqueue)

    def cause_problems():
        global thread_continuing
        while thread_continuing:
            x = int(raw_input())
            inqueue.put(("swing", { "player": x }))

    # put something new on the inqueue every 10 seconds
    thread = Thread(target = cause_problems)
    thread.start()

    # run the show
    try:
        show.run(framerate=2)
    except KeyboardInterrupt:
        global thread_continuing
        thread_continuing = False

if __name__ == "__main__":
    main()
