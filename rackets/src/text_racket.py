# text_racket.py
# aoneill - 04/24/17

from libs import psmoveapi
import racket

class TextRacket(racket.Racket):
  '''
  Text-based racket implementation for testing a simple sequence of
  racket motions
  '''

  def hand_to_string(self, hand):
    # Convenience method to display handedness
    return '(left)' if(hand == racket.Handedness.LEFT) else '(right)'

  def on_idle(self, controller, hand):
    # On idle, the player should see a white ball and have no rumble
    print 'idle', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(1.0, 1.0, 1.0)
    controller.rumble = 0

  def on_backswing(self, controller, hand):
    # On a backswing, the player should see a red ball and have some rumble
    print 'backswing', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(1.0, 0, 0)
    controller.rumble = 0.33

  def on_transition(self, controller, hand):
    # On a transition, the player should see a green ball and have more rumble
    print 'transition', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(0, 1.0, 0)
    controller.rumble = 0.66

  def on_swing(self, controller, hand):
    # On a transition, the player should see a blue ball and have max rumble
    print 'swing', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(0, 0, 1.0)
    controller.rumble = 1.0

  def on_init(self, controller):
    print 'Controller', controller, 'connected!'

  def on_refresh(self, controller):
    # This is available for doing other house-keeping, but is unused right now
    pass

  def on_leave(self, controller):
    print 'Controller', controller, 'disconnected!'
