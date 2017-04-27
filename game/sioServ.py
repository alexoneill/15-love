import socketio
import Queue
import eventlet
import eventlet.wsgi
from flask import Flask

sio = socketio.Server()
app = Flask(__name__)

inqueue = Queue.Queue()
outqueue = Queue.Queue()


# Not for the server, but this is what the game loop should call to send rumble
def rumble(data):
    sio.emit('rumble', data)  # Data is the player number and rumble val


@sio.on('connect')
def connect(sid, environ):
    print("connected", sid)
    '''rumbleData = {'player':     1,
                  'rumbleVal':  200}
    inqueue.put(rumbleData)'''


@sio.on('swing')
def getSwing(sid, swingData):
    print("got swing:", swingData)  # swingData is a list conating...
    inqueue.put(('swing', swingData))  # puts the swingdata on the inqueue

    ''' rumble callback test
    rumbleData = {'player':     1,
                  'rumbleVal':  200}
    sio.emit('rumble', rumbleData)'''


@sio.on('disconnect')
def disconnect(sid):
    print('disconnected', sid)


if __name__ == '__main__':
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('localhost', 8000)), app)

''' Does not work to get inqueue data
    while(1):
        data = outqueue.get()
        print(data)
        if (data is not None):
            print('got data')
            rumble(data)'''
