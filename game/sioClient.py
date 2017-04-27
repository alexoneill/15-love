from socketIO_client import SocketIO, LoggingNamespace


def on_connect():
    print('connected')


def on_disconnect():
    print('disconnected')


def on_reconnect():
    print('reconnected')


def getRumble(data):
    # Unpack args, rumble is a dict conatining player and rumbleVal.s
    player = data['player']
    rumbleVal = data['rumbleVal']
    print('rumbling player %d' % player, rumbleVal)

    # Pass rumble to racquet
    # insert code here to pass rumble val along


socketIO = SocketIO('localhost', 8000, LoggingNamespace)  # Sets up connection

# Link events to handlers
socketIO.on('connect', on_connect)
socketIO.on('disconnect', on_disconnect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('rumble', getRumble)


###############################################################################
# Test, sends 2 swings with junk data and disconnects
###############################################################################
swingdata = [1, 2, 3]
socketIO.emit('swing', swingdata)
socketIO.wait(seconds=1)
socketIO.emit('swing', 2)
socketIO.disconnect()
