#!/usr/bin/python2
# client.py
# nroberts - 4/24/2017

import socket
import pickle
from threading import Thread

thread_continuing = True

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 8081))

    def write():
        global thread_continuing
        while thread_continuing:
            x = raw_input()
            if x == "1":
                obj = ("swing", { "player": 1 })
            else:
                obj = ("swing", { "player": 2 })
            data = pickle.dumps(obj)
            client.send(data)

    def read():
        global thread_continuing
        while thread_continuing:
            x = client.recv(1024)
            print pickle.loads(x)

    write_thread = Thread(target=write)
    write_thread.start()
    try:
        read()
    finally:
        global thread_continuing
        thread_continuing = False

if __name__ == "__main__":
    main()
