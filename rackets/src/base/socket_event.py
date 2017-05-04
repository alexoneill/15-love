# socket_event.py
# aoneill - 05/02/17

import Queue
import pickle
import threading

class EventListener(threading.Thread):
  '''
  Simple, threaded, network event listener
  '''
  MSG_LEN = 4096

  def __init__(self, sock):
    super(EventListener, self).__init__()

    # Instance variables
    self.sock = sock
    self._queue = Queue.Queue()

    # Start immediately
    self.start()

  def has(self):
    # Determine if there are events available
    return (not self._queue.empty())

  def get(self, blocking = False):
    # Get an event from the event queue
    return self._queue.get(blocking)

  def run(self):
    # Continually listen to the network connection
    while(True):
      data = self.sock.recv(EventListener.MSG_LEN)
      if(data == ''):
        return

      # Load the data, append to the queue
      data = pickle.loads(data)
      print 'EventListener:', data

      self._queue.put(data)


class EventSender(threading.Thread):
  '''
  Simple, threaded, network event sender
  '''
  MSG_LEN = 4096

  def __init__(self, sock):
    super(EventSender, self).__init__()

    # Instance variables
    self.sock = sock
    self._queue = Queue.Queue()

    # Start immediately
    self.start()

  def put(self, data):
    # Mark data as ready to be sent
    return self._queue.put(data)

  def run(self):
    # Continually wait for data to send
    while(True):
      # Get data to send
      data = self._queue.get(True)
      print 'EventSender:', data

      # Send it
      data = pickle.dumps(data)
      self.sock.send(data)


