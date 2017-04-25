#!/usr/bin/python2
# server.py
# nroberts - 4/24/2017

import socket
import sys
import pickle
from tennis_show import TennisShow
from bridge import Bridge
import Queue
from threading import Thread

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


thread_continuing = True

def main(bridge):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('localhost', 8081))
    serversocket.listen(1) # max 1 connection
    connection, address = serversocket.accept() # block until client connects

    inqueue = Queue.Queue()
    outqueue = Queue.Queue()

    def read():
        global thread_continuing
        while thread_continuing:
            buf = connection.recv(1024)
            if len(buf) > 0:
                message = pickle.loads(buf)
                outqueue.put(message)

    def write():
        global thread_continuing
        while thread_continuing:
            data = inqueue.get() # Block until we get something
            pickled = pickle.dumps(data)
            connection.send(pickled)

    readthread = Thread(target=read)
    writethread = Thread(target=write)

    show = TennisShow(bridge(), inqueue=outqueue, outqueue=inqueue)

    readthread.start()
    writethread.start()

    try:
        show.run(framerate=40)
    finally:
        global thread_continuing
        thread_continuing = False
        connection.close()
        serversocket.close()

if __name__ == "__main__":
    bridge = PauschBridge if "-p" in sys.argv else TerminalBridge
    main(bridge)
