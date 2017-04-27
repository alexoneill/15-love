import socketio
import Queue
import eventlet
import eventlet.wsgi
from flask import Flask

###############################################################################
'''SocketIO based server for 15-Love

Handles events from rackets and sets up wrappers to communicate with the
racket host computer. Events and cooresponding data structures defined in
sio_spec.txt'''
###############################################################################

# Define server and queues
sio = socketio.Server()
app = Flask(__name__)

inqueue = Queue.Queue()
outqueue = Queue.Queue()


###############################################################################
# Emit wrappers, to be called in the game to send events
###############################################################################
def init_color_reject():
    sio.emit('init_color_reject')


def init_color_confrim(color):
    sio.emit('init_color_confirm', color)


def game_missed_ball():
    sio.emit('game_missed_ball')


def game_hit_ball(hitData):
    sio.emit('game_hit_ball', hitData)


def game_is_server():
    sio.emit('game_is_server')


def game_over(is_winner):
    sio.emit('game_over', is_winner)


###############################################################################
# Event Handlers
###############################################################################
@sio.on('connect')
def connect(sid, environ):
    print("connected", sid)


@sio.on('init_color_choice')
def init_color_choice(sid, colorData):
    inqueue.add(('init_color_choice', colorData))


@sio.on('game_swing')
def game_swing(sid, swingData):
    inqueue.put(('swing', swingData))


@sio.on('game_reset')
def game_reset(sid):
    inqueue.add(('game_reset', None))


@sio.on('disconnect')
def disconnect(sid):
    print('disconnected', sid)


###############################################################################
# Run
###############################################################################
if __name__ == '__main__':
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('localhost', 8000)), app)
