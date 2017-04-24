# text_racket.py
# aoneill - 04/24/17

from libs import psmoveapi
import racket

class TextRacket(racket.Racket):
  def hand_to_string(self, hand):
    return '(left)' if(hand == racket.Handedness.LEFT) else '(right)'

  def on_idle(self, controller, hand):
    print 'idle', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(1.0, 1.0, 1.0)
    controller.rumble = 0

  def on_backswing(self, controller, hand):
    print 'backswing', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(1.0, 0, 0)
    controller.rumble = 0.33

  def on_transition(self, controller, hand):
    print 'transition', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(0, 1.0, 0)
    controller.rumble = 0.66

  def on_swing(self, controller, hand):
    print 'swing', self.hand_to_string(hand)
    controller.color = psmoveapi.RGB(0, 0, 1.0)
    controller.rumble = 1.0

  def on_connect(self, controller):
    print 'Controller', controller, 'connected!'

  def on_disconnect(self, controller):
    print 'Controller', controller, 'disconnected!'
