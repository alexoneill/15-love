# text_racket.py
# aoneill - 04/24/17

import math
import mock
import socketIO_client as sio

from libs import psmoveapi
import racket

class Event(object):
  def __init__(self, end_time, action):
    self.end_time = end_time
    self.action = action

  def done(self):
    return (time.time() >= self.end_time)

  def do(self, *args):
    if(not self.done()):
      self.action(self.end_time - time.time(), *args)

class GameState(object):
  PRE_GAME = 0
  COLOR_SELECTION = 1
  COLOR_WAIT = 2
  START_WAIT = 3
  SERVER = 4
  GAMEPLAY = 5
  WON_RALLY = 6
  LOST_RALLY = 7
  END_GAME_WIN = 8
  END_GAME_LOST = 9

class SIORacket(racket.Racket):
  '''
  socketio-based racket for gameplay.

  This class includes many different events for actual gameplay!
  '''

  COLORS = {
      psmoveapi.Button.SQUARE:   (255.0 / 255.0, 105.0 / 255.0, 180.0 / 255.0),
      psmoveapi.Button.TRIANGLE: ( 64.0 / 255.0, 255.0 / 255.0, 64.0 / 255.0),
      psmoveapi.Button.CROSS:    (24.0 / 255.0, 135.0 / 255.0, 189.0 / 255.0),
      psmoveapi.Button.CIRCLE:   (255.0 / 255.0,  168.0 / 255.0,  24.0 / 255.0)
    }

  COLOR_LOSE  = (1.0, 0, 0)
  COLOR_WIN   = (0, 1.0, 0)
  COLOR_CLEAR = (1.0, 1.0, 1.0)

  COLOR_CONFIRM_TIME = 1
  COLOR_REJECT_TIME = 1
  SERVER_TIME = 1
  LOST_TIME = 0.5
  HIT_TIME = 0.5
  WON_RALLY_TIME = 2
  OVER_TIME = 3
  RESET_TIME = 1

  def __init__(self, sio_host, sio_port, player_num):
    super(SIORacket, self).__init__()

    # Save parameters
    self.sio_host = sio_host
    self.sio_port = sio_port
    self.player_num = player_num

    # socketio config
    # self._sio = sio.socketio(self.sio_host, self.sio_port)
    self._sio = type('', (), {})
    def print2(*args):
      print args

    self._sio.on = mock.Mock(side_effect = print2)
    self._sio.emit = mock.Mock(side_effect = print2)

    # socketio callbacks
    # Basic
    self._sio.on('connect', self.on_sio_connect)
    self._sio.on('disconnect', self.on_sio_disconnect)

    # Game-based - Listening
    self._sio.on('init_color_reject', self.on_sio_init_color_reject)
    self._sio.on('init_color_confirm', self.on_sio_init_color_confirm)
    self._sio.on('game_is_server', self.on_sio_game_is_server)
    self._sio.on('game_missed_ball', self.on_sio_game_missed_ball)
    self._sio.on('game_hit_ball', self.on_sio_game_hit_ball)
    self._sio.on('game_won_rally', self.on_sio_game_won_rally)
    self._sio.on('game_over', self.on_sio_game_over)

    # Other parameters
    self.state = GameState.PRE_GAME
    self.state_data = None
    self.color_choice = None
    self.enable_swings = False

    print 'socketio: init'

  ################################ Helpers #####################################

  def generic_flash(self, freq = 1, rumble = True, color = True,
      invert_color = False, invert_rumble = False, scale = 1.0):
    def flash(time, controller, color_rgb):
      power = (1 - math.cos(time * (2 * math.pi) * freq))/2
      power = min(1.0, max(0.0, power * scale))

      color_power = power if(invert_color) else (1 - power)
      rumble_power = (1 - power) if(invert_rumble) else power
      color_flash = tuple(map(lambda x: x * color_power, list(color_rgb)))

      if(color):
        controller.color = psmoveapi.RGB(*color_flash)
      if(rumble):
        controller.rumble = rumble_power

    return flash

  ######################## socketio Housekeeping ###############################

  def on_sio_connect(self):
    print 'socketio: Connected'

  def on_sio_disconnect(self):
    print 'socketio: Disconnected'

  ######################### socketio Listeners #################################

  def on_sio_init_color_reject(self):
    self.enable_swings = False

    self.state = GameState.COLOR_SELECTION
    self.state_data = {
        'events': [
            (Event(SIORacket.COLOR_CONFIRM_TIME,
                self.generic_flash(color = False)), None)
          ]
      }

  def on_sio_init_color_confirm(self):
    self.enable_swings = True

    self.state = GameState.START_WAIT
    self.state_data = {
        'events': [
            (Event(SIORacket.COLOR_REJECT_TIME,
                self.generic_flash(freq = 3)), None)
          ]
      }

  def on_sio_game_is_server(self):
    self.enable_swings = True

    self.state = GameState.SERVER
    self.state_data = {
        'events': [
            (Event(SIORacket.SERVER_TIME, self.generic_flash(freq = 2)), None)
          ]
      }

  def on_sio_game_missed_ball(self):
    self.enable_swings = True

    self.state = GameState.LOST_RALLY
    self.state_data = {
        'events': [
            (Event(SIORacket.LOST_TIME,
                self.generic_flash(freq = 2)), SIORally.COLOR_LOSE)
          ]
      }

  def on_sio_game_hit_ball(self, data):
    strength = data['strength']

    self.enable_swings = True

    self.state = GameState.HIT_BALL
    self.state_data = {
        'events': [
            (Event(SIORacket.HIT_TIME,
                self.generic_flash(scale = strength)), None)
          ]
      }

  def on_sio_game_won_rally(self):
    self.state = GameState.WON_RALLY
    self.state_data = {
        'events': [
            (Event(SIORacket.WON_RALLY_TIME,
                self.generic_flash(freq = 2)), SIORally.COLOR_WIN)
          ]
      }

  def on_sio_game_over(self, data):
    is_winner = data['is_winner']

    self.enable_swings = True

    color = SIORacket.COLOR_WIN
    if(is_winner):
      self.state = GameState.END_GAME_WIN
    else:
      color = SIORacket.COLOR_LOSE
      self.state = GameState.END_GAME_LOSE

    self.state_data = {
        'events': [
            (Event(SIORacket.OVER_TIME, self.generic_flash(freq = 3)), color),
            (Event(SIORacket.RESET_TIME, self.generic_flash()),
                SIORacket.COLOR_CLEAR)
          ]
      }

  ########################### socketio Emits ###################################

  def sio_init_color_choice(self, color):
    self._sio.emit('init_color_choice', {
        'color': color
      })

  def sio_game_swing(self, hand, strength):
    self._sio.emit('init_color_choice', {
        'player_num': self.player_num,
        'hand': (0 if(hand == racket.Handedness.LEFT) else 1),
        'strength': stength
      })

  ############################ Racket Events ###################################

  def on_idle(self, controller, hand):
    # On idle, the player should see a white ball and have no rumble
    controller.color = psmoveapi.RGB(*self.color_choice)
    controller.rumble = 0

  def on_backswing(self, controller, hand):
    # On a backswing, the player should see a red ball and have some rumble
    controller.rumble = 0.33

  def on_swing(self, controller, hand, strength):
    # On a transition, the player should see a blue ball and have max rumble
    controller.rumble = 1.0

    # Send the swing
    self.sio_game_swing(hand, strength)
    print 'racket: Swing, %f' % strength

  ############################# Button Events ##################################

  def on_button(self, controller, buttons):
    print 'psmove:', buttons, 'pressed'

    if(psmoveapi.Button.PS in buttons):
      self.state = (self.state + 1) % (GameState.END_GAME_LOST + 1)
      strs = {
          0: 'PRE_GAME',
          1: 'COLOR_SELECTION',
          2: 'COLOR_WAIT',
          3: 'START_WAIT',
          4: 'SERVER',
          5: 'GAMEPLAY',
          6: 'WON_RALLY',
          7: 'LOST_RALLY',
          8: 'END_GAME_WIN',
          9: 'END_GAME_LOST'
        }
      print strs[self.state]
      return

    if(self.state == GameState.COLOR_SELECTION):
      choices = (psmoveapi.Button.SQUARE, psmoveapi.Button.TRIANGLE,
        psmoveapi.Button.CROSS, psmoveapi.Button.CIRCLE)

      for button in choices:
        if(button in buttons):
          self.color_choice = SIORacket.COLORS[button]
          controller.color = psmoveapi.RGB(*self.color_choice)
          return

    if((self.color_choice is not None) and (psmoveapi.Button.MOVE in buttons)):
      self.sio_init_color_choice(self.color_choice)
      self.state = GameState.COLOR_WAIT

  ######################### Housekeeping Events ################################

  def on_init(self, controller):
    print 'psmove:', controller, 'connected!'
    controller.color = psmoveapi.RGB(*SIORacket.COLOR_CLEAR)

  def on_leave(self, controller):
    print 'psmove:', controller, 'disconnected!'

  def on_refresh(self, controller, swing_state):
    # Here is where most of the day-to-day logic takes effect
    if(self.state == GameState.PRE_GAME
        or self.state == GameState.COLOR_SELECTION
        or self.state == GameState.COLOR_WAIT
        or self.state == GameState.START_WAIT):
      return self.enable_swings

    # To be changed below
    next_state = None
    enable_swings = False

    if(self.state == GameState.SERVER
        or self.state == GameState.WON_RALLY
        or self.state == GameState.LOST_RALLY):
      next_state = GameState.GAMEPLAY

    elif(self.state == GameState.GAMEPLAY):
      enable_swings = True

    # elif(self.state == GameState.END_GAME_WIN
    #     or self.state == GameState.END_GAME_LOST):
    #   pass

    if(self.state_data is not None):
      if('events' in self.state_data):
        events = self.state_data['events']

        if(len(events) == 0 or events[0].done()):
          if(next_state is not None):
            self.state = next_state
            del self.state_data['events']
        else:
          (event, color) = events[0]
          color = self.color_choice if(color is None) else color
          event.do(controller, color)

      elif(len(self.state_data) == 0):
        self.state_data = None

    return enable_swings

  def exit(self):
    self.sio.disconnect()
