# racket.py
# aoneill - 04/24/17

from libs import psmoveapi

class SwingState(object):
  IDLE = 0
  BACKSWING = 1
  TRANSITION = 2
  SWING = 3

class Handedness(object):
  LEFT = 0
  RIGHT = 1

class Racket(psmoveapi.PSMoveAPI):
  SWING_SIZE = 2.0
  SWING_PAUSE = 1.0

  def __init__(self):
    super(Racket, self).__init__()

    self._state = SwingState.IDLE
    self._hand = Handedness.RIGHT

  def _step_backswing(self, controller):
    if(self._state == SwingState.IDLE):
      if(controller.accelerometer.length() > Racket.SWING_SIZE):
        self._state = SwingState.BACKSWING
        self._hand = (
            Handedness.LEFT if(controller.gyroscope.z > 0) else Handedness.RIGHT
          )

        (self.on_backswing or (lambda *args: None))(controller, self._hand)

  def _step_transition(self, controller):
    if(self._state == SwingState.BACKSWING):
      if(controller.accelerometer.length() < Racket.SWING_PAUSE):
        self._state = SwingState.TRANSITION

        (self.on_transition or (lambda *args: None))(controller, self._hand)

  def _step_swing(self, controller):
    if(self._state == SwingState.TRANSITION):
      if(controller.accelerometer.length() > Racket.SWING_SIZE):
        self._state = SwingState.SWING

        (self.on_swing or (lambda *args: None))(controller, self._hand)

  def _step_idle(self, controller):
    if(self._state == SwingState.SWING):
      if(controller.accelerometer.length() < Racket.SWING_PAUSE):
        self._state = SwingState.IDLE

        (self.on_idle or (lambda *args: None))(controller, self._hand)

  def _step_state(self, controller):
    self._step_backswing(controller)
    self._step_transition(controller)
    self._step_swing(controller)
    self._step_idle(controller)

  def on_update(self, controller):
    self._step_state(controller)
