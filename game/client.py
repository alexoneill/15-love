#!/usr/bin/python2
# client.py
# nroberts - 4/24/2017

import socket
import pickle

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 8081))
    while True:
        x = raw_input()
        if x == "1":
            obj = ("swing", { "player": 1 })
        else:
            obj = ("swing", { "player": 2 })
        data = pickle.dumps(obj)
        client.send(data)

if __name__ == "__main__":
    main()
