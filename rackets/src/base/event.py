# sio_racket.py
# aoneill - 04/28/17

import time

class Event(object):
  '''
  Generic time-based events, where a parameterized action is executed
  when requested.

  The associated action takes a time value (bounded to [0, 1]) as the
  first argument, and arbitrary values for the remainder of the arguments.
  '''
  def __init__(self, duration, action):
    self.duration = duration
    self.action = action

    # Internal state
    self._started = False
    self._stopped = False
    self._start_time = None

  def start(self):
    # Mark the event as started
    self._started = True
    self._start_time = time.time()

  def stop(self):
    # Mark the event as stopped, regardless if the time has come
    self._stopped = True

  def done(self):
    # Determine if the event is over
    return self._stopped or (
        (self._started) and (time.time() >= self._start_time + self.duration)
      )

  def do(self, *args):
    # Run the action of the event

    # Start the event if not yet started
    if(not self._started):
      self.start()
      print 'event:', self

    # Do the action if still defined
    if(not self.done()):
      self.action((time.time() - self._start_time) / self.duration, *args)

  def __str__(self):
    if(self.action):
      return '%s{duration = %d, action = %s}' % (
          self.__class__.__name__, self.duration, self.action.__name__)
    else:
      return '%s{duration = %d, action = None}' % (
          self.__class__.__name__, self.duration)
