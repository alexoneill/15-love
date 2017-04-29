# sio_racket.py
# aoneill - 04/28/17

from libs import psmoveapi

from src.base import event

class ClearEvent(event.Event):
  '''
  An event to clear a given PSMove controller.

  This only executes once.
  '''
  def __init__(self, clear_rumble = True, clear_color = False):
    # Initialize with dummy variables
    super(ClearEvent, self).__init__(0, None)

    self.clear_rumble = clear_rumble
    self.clear_color = clear_color

    # Internal state
    self._done = False

  def done(self):
    # Done-ness is based on whether or not we have executed the do statement yet
    return self._done

  def do(self, controller, color):
    # Reset various parts of the controller if requested
    print 'event:', self

    if(self.clear_rumble):
      controller.rumble = 0

    if(self.clear_color):
      controller.color = psmoveapi.RGB(*color)

    # Mark as done
    self._done = True

