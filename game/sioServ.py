#!/usr/bin/python2

import socketio
#import eventlet
#import eventlet.wsgi
from flask import Flask
import threading

import Queue
from tennis_show import TennisShow
import current_bridge

###############################################################################
'''SocketIO based server for 15-Love

Handles events from rackets and sets up wrappers to communicate with the
racket host computer. Events and cooresponding data structures defined in
sio_spec.txt'''
###############################################################################

# Define server and queues
sio = socketio.Server(async_mode='threading')
app = Flask(__name__)
inqueue = Queue.Queue()
thread = None

###############################################################################
# Emit wrappers, to be called in the game to send events
###############################################################################
class OutQueue:
    def put(self, event):
        global sio
        print "Emitting event to client: %s" % str(event)
        sio.emit(*event)

show = TennisShow(current_bridge.bridge(), inqueue=inqueue, outqueue=OutQueue())

###############################################################################
# Event Handlers
###############################################################################
@sio.on('connect')
def connect(sid, environ):
    print("connected", sid)

@sio.on('init_color_choice')
def init_color_choice(sid, colorData):
    inqueue.put(('init_color_choice', colorData))


@sio.on('game_swing')
def game_swing(sid, swingData):
    inqueue.put(('game_swing', swingData))


@sio.on('game_reset')
def game_reset(sid):
    inqueue.put(('game_reset', None))


@sio.on('disconnect')
def disconnect(sid):
    print('disconnected', sid)

def run_server():
    app.run(threaded=True, host='0.0.0.0', port=8000)

###############################################################################
# Run
###############################################################################
if __name__ == '__main__':
    print "Madeshow"

    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    show.run(framerate=40)
