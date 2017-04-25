# racket.py
# aoneill - 04/24/17

from libs import psmoveapi

class SwingState(object):
  '''
  Enum-like object to store the swing state
  '''
  IDLE = 0
  BACKSWING = 1
  SWING = 2

class Handedness(object):
  '''
  Enum-like object to store the handedness of the swing
  '''
  LEFT = 0
  RIGHT = 1

class Racket(psmoveapi.PSMoveAPI):
  '''
  Wrapper around the PSMoveAPI base class to give racket-based callbacks,
  rather than lower-level interactions.
  '''

  # Thresholds for swing strength
  SWING_PAUSE = 1.5
  TRIGGER_BACK = 0.5

  def __init__(self):
    super(Racket, self).__init__()

    # Initialize internal state mahine
    self._state = SwingState.IDLE
    self._hand = Handedness.RIGHT

  def _step_backswing(self, controller):
    # Transition from IDLE to BACKSWING if it makes sense
    if(self._state == SwingState.IDLE):
      if(controller.accelerometer.length() > Racket.SWING_PAUSE):
        if(controller.trigger > Racket.TRIGGER_BACK):
          self._state = SwingState.BACKSWING

          # Assume that the hand stays the same throughout the swing
          # It would be awkward for the player otherwise
          self._hand = (
              Handedness.LEFT if(controller.gyroscope.z > 0)
                else Handedness.RIGHT
            )

          # Call our callback if defined
          (self.on_backswing or (lambda *args: None))(controller, self._hand)

  def _step_swing(self, controller):
    # Transition from TRANSITION to SWING if it makes sense
    if(self._state == SwingState.BACKSWING):
      if(controller.accelerometer.length() > Racket.SWING_PAUSE):
        if(controller.trigger < Racket.TRIGGER_BACK):
          self._state = SwingState.SWING

          # Call our callback if defined
          (self.on_swing or (lambda *args: None))(controller, self._hand)

  def _step_idle(self, controller):
    # Transition from SWING to IDLE if it makes sense
    if(self._state == SwingState.SWING):
      if(controller.accelerometer.length() < Racket.SWING_PAUSE):
        self._state = SwingState.IDLE

        # Call our callback if defined
        (self.on_idle or (lambda *args: None))(controller, self._hand)

  def _step_state(self, controller):
    # Step through the states
    self._step_backswing(controller)
    self._step_swing(controller)
    self._step_idle(controller)

  def on_connect(self, controller):
    # Call our callback if defined
    (self.on_init or (lambda *args: None))(controller)

  def on_disconnect(self, controller):
    # Call our callback if defined
    (self.on_leave or (lambda *args: None))(controller)

  def on_update(self, controller):
    self._step_state(controller)

    # Call our callback if defined
    (self.on_refresh or (lambda *args: None))(controller)
