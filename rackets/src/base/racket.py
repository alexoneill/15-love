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

  # Limits for swing strength
  SWING_MAX_STRENGTH = 10.0
  SWING_MIN_STRENGTH = SWING_PAUSE

  def __init__(self):
    super(Racket, self).__init__()

    # Initialize internal state machine
    self._state = SwingState.IDLE
    self._hand = Handedness.RIGHT
    self._disable = False
    self._enable = False

  def _optional_callback(self, name, *args):
    # Given the name of a function which may exist, call it if it does with the
    # supplied arguments
    if(hasattr(self, name)):
      return getattr(self, name)(*args)

    return None

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
          self._optional_callback('on_backswing', controller, self._hand)

  def _step_swing(self, controller):
    # Transition from TRANSITION to SWING if it makes sense
    if(self._state == SwingState.BACKSWING):
      if(controller.accelerometer.length() > Racket.SWING_PAUSE):
        if(controller.trigger < Racket.TRIGGER_BACK):
          self._state = SwingState.SWING

          # Calculate strength
          strength = min(Racket.SWING_MAX_STRENGTH,
              max(Racket.SWING_MIN_STRENGTH, controller.accelerometer.length()))
          strength = ((strength - Racket.SWING_MIN_STRENGTH) /
              (Racket.SWING_MAX_STRENGTH - Racket.SWING_MIN_STRENGTH))

          # Call our callback if defined
          (self.on_swing or (lambda *args: None))(
              controller, self._hand, strength)

  def _step_idle(self, controller):
    # Transition from SWING to IDLE if it makes sense
    if(self._state == SwingState.SWING):
      if(controller.accelerometer.length() < Racket.SWING_PAUSE):
        self._state = SwingState.IDLE

        # Call our callback if defined
        self._optional_callback('on_idle', controller, self._hand)

  def _step_state(self, controller):
    # Step through the states
    self._step_backswing(controller)
    self._step_swing(controller)
    self._step_idle(controller)

  def _get_button(self, controller):
    # See which buttons are pressed
    buttons = (psmoveapi.Button.TRIANGLE, psmoveapi.Button.CIRCLE,
        psmoveapi.Button.CROSS, psmoveapi.Button.SQUARE,
        psmoveapi.Button.SELECT, psmoveapi.Button.START,
        psmoveapi.Button.PS, psmoveapi.Button.MOVE)

    pressed = set()
    held = set()
    released = set()

    for button in buttons:
      if(controller.now_pressed(button)):
        pressed.add(button)

      if(controller.still_pressed(button)):
        held.add(button)

      if(controller.now_released(button)):
        released.add(button)

    # Give the collection of buttons
    if(pressed | held | released):
      return (pressed, held, released)

    return None

  def on_connect(self, controller):
    # Call our callback if defined
    self._optional_callback('on_init', controller)

  def on_disconnect(self, controller):
    # Call our callback if defined
    self._optional_callback('on_leave', controller)

  def on_update(self, controller):
    # Enable swing events if requested
    if(self._enable):
      self._step_state(controller)

    # Create a button event
    buttons = self._get_button(controller)
    if(buttons is not None):
      self._optional_callback('on_button', controller, *buttons)

    # Call our callback if defined
    enable = self._optional_callback('on_refresh', controller, self._state)
    if(enable is not None):
      self._enable = enable

