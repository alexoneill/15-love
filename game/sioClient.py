from socketIO_client import SocketIO, LoggingNamespace


def on_connect():
    print('connected')


def on_disconnect():
    print('disconnect')


def on_reconnect():
    print('reconnect')


def on_color_response(*args):
    print('got color', args)


socketIO = SocketIO('localhost', 8000, LoggingNamespace)
socketIO.on('connect', on_connect)
socketIO.on('disconnect', on_disconnect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('color', on_color_response)

# Listen
socketIO.emit('swing', 1)
socketIO.wait(seconds=1)
socketIO.emit('swing', 2)
socketIO.wait()
