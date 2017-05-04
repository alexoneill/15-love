#!/usr/bin/python2
# test.py
# nroberts 04/10/2017
# Instead of lighting up a bridge, we light up the terminal

from tennis_show import TennisShow
import current_bridge
from threading import Thread
import Queue
from colors import Colors

thread_continuing = True

class OutQueue:
    def put(self, event):
        print "Put in outqueue: %s" % str(event)

def main(bridge):
    global thread_continuing
    print "Usage: Press 1 for player 1 swing, 2 for player 2 swing (followed by Enter)"
    print "To quit, press Ctrl+C and then Enter"
    inqueue = Queue.Queue()
    outqueue = OutQueue()
    show = TennisShow(bridge(), inqueue=inqueue, outqueue=outqueue)

    def cause_problems():
        global thread_continuing
        while thread_continuing:
            inp = raw_input()
            if inp == "r":
                inqueue.put(("game_reset", None))
                continue
            try:
                x = int(inp[0])
                if len(inp) > 1:
                    if inp[1] == "s":
                        inqueue.put(("init_color_choice", { "player_num": x, "color": Colors.RED }))
                    elif inp[1] == "t":
                        inqueue.put(("init_color_choice", { "player_num": x, "color": Colors.GREEN }))
                    elif inp[1] == "c":
                        inqueue.put(("init_color_choice", { "player_num": x, "color": Colors.PURPLE }))
                    elif inp[1] == "x":
                        inqueue.put(("init_color_choice", { "player_num": x, "color": Colors.SKY_BLUE }))
                else:
                    inqueue.put(("game_swing", { "player_num": x, "hand": 1, "strength": 1.0 }))
            except:
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
    main(current_bridge.bridge)
