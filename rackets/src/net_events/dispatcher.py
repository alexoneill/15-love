# dispatcher.py
# aoneill - 05/02/17

import threading

from src.base import socket_event

class EventDispatcher(threading.Thread):
  def __init__(self, sock):
    super(EventDispatcher, self).__init__()

    # Instance variables
    self._listener = socket_event.EventListener(sock)
    self._events = {}

    # Start immediately
    self.start()

  def on(self, event, func):
    # Record an event responder
    self._events[event] = func

  def run(self):
    # Continually wait for events
    while(True):
      (id_str, data) = self._listener.get(blocking = True)

      # Try to find an event listener
      if(id_str in self._events):
        func = self._events[id_str]

        # Call the handler
        print 'EventDispatcher:', (func.__name__, data)
        func(data)


