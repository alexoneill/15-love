import socketio
import Queue
import eventlet
import eventlet.wsgi
from flask import Flask

sio = socketio.Server()
app = Flask(__name__)

inqueue = Queue.Queue()
outqueue = Queue.Queue()


###############################################################################
# Emit wrappers, to be called in the game to send events
###############################################################################
def init_color_reject():
    sio.emit('init_color_reject', None)


def init_color_confrim(color):
    sio.emit('init_color_confirm', color)


def game_missed_ball():
    sio.emit('game_missed_ball', None)


def game_hit_ball(hitData):
    sio.emit('game_hit_ball', hitData)


def game_is_server():
    sio.emit('game_is_server', None)


def game_over(is_winner):
    sio.emit('game_over', is_winner)


###############################################################################
# Event Handlers (what the server is listening for)
###############################################################################
@sio.on('connect')
def connect(sid, environ):
    print("connected", sid)


@sio.on('swing')
def get_swing(sid, swingData):
    print("got swing:", swingData)  # swingData is a list conating...
    inqueue.put(('swing', swingData))  # puts the swingdata on the inqueue


@sio.on('disconnect')
def disconnect(sid):
    print('disconnected', sid)


if __name__ == '__main__':
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('localhost', 8000)), app)
