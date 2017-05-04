#!/usr/bin/python2
# server.py
# nroberts - 4/24/2017

import socket
import sys
import pickle
from tennis_show import TennisShow
import current_bridge
import Queue
from threading import Thread

thread_continuing = True

def main(bridge, port = '8000'):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('0.0.0.0', int(port)))
    serversocket.listen(2) # max 1 connection

    inqueue = Queue.Queue()
    outqueue = Queue.Queue()

    show = TennisShow(bridge(), inqueue=outqueue, outqueue=inqueue)
    show_thread = Thread(target=lambda: show.run(framerate=40))
    show_thread.start()

    conn1, addr1 = serversocket.accept() # block until client connects
    print "Accepted %s" % conn1
    conn2, addr2 = serversocket.accept()
    print "Accepted %s" % conn2

    def read1():
        global thread_continuing
        while thread_continuing:
            buf = conn1.recv(4096)
            if len(buf) > 0:
                message = pickle.loads(buf)
                outqueue.put(message)

    read1thread = Thread(target=read1)
    read1thread.start()

    def read2():
        global thread_continuing
        while thread_continuing:
            buf = conn2.recv(4096)
            if len(buf) > 0:
                message = pickle.loads(buf)
                outqueue.put(message)

    read2thread = Thread(target=read2)

    def write():
        global thread_continuing
        while thread_continuing:
            data = inqueue.get() # Block until we get something
            print "Emitting to clients %s" % str(data)
            pickled = pickle.dumps(data)
            conn1.send(pickled)
            conn2.send(pickled)

    writethread = Thread(target=write)
    writethread.start()

    try:
        read2thread.run()
    finally:
        global thread_continuing
        thread_continuing = False
        conn1.close()
        conn2.close()
        serversocket.close()

if __name__ == "__main__":
    main(current_bridge.bridge, *sys.argv[1:])

