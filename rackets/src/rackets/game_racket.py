# text_racket.py
# aoneill - 04/24/17

from libs import psmoveapi
from src.base import racket

import pickle

class GameRacket(racket.Racket):
  '''
  Text-based racket implementation for testing a simple sequence of
  racket motions
  '''

  def __init__(self, socket, player_num):
    super(GameRacket, self).__init__()

    self.socket = socket
    self.player_num = player_num

  def on_idle(self, controller, hand):
    # On idle, the player should see a white ball and have no rumble
    controller.color = psmoveapi.RGB(1.0, 1.0, 1.0)
    controller.rumble = 0

  def on_backswing(self, controller, hand):
    # On a backswing, the player should see a red ball and have some rumble
    controller.color = psmoveapi.RGB(1.0, 0, 0)
    controller.rumble = 0.33

  def on_transition(self, controller, hand):
    # On a transition, the player should see a green ball and have more rumble
    controller.color = psmoveapi.RGB(0, 1.0, 0)
    controller.rumble = 0.66

  def on_swing(self, controller, hand):
    # On a transition, the player should see a blue ball and have max rumble
    controller.color = psmoveapi.RGB(0, 0, 1.0)
    controller.rumble = 1.0

    # Send swing information
    obj = ("swing", { "player": self.player_num })
    data = pickle.dumps(obj)
    self.socket.send(data)

    print 'Sent swing packet!'

  def on_init(self, controller):
    print 'Controller', controller, 'connected!'
    controller.color = psmoveapi.RGB(1.0, 1.0, 1.0)

  def on_refresh(self, controller):
    pass

  def on_leave(self, controller):
    print 'Controller', controller, 'disconnected!'
