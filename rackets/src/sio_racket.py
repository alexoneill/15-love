# sio_racket.py
# aoneill - 04/28/17

import math
import mock
import random
import socketIO_client as sio
import time

from libs import psmoveapi
import racket

class Event(object):
  def __init__(self, duration, action):
    self.duration = duration
    self.action = action

    self._started = False
    self._stopped = False
    self._start_time = None

  def start(self):
    print 'event:', self

    self._started = True
    self._start_time = time.time()

  def stop(self):
    self._stopped = True

  def done(self):
    return self._stopped or (
        (self._started) and (time.time() >= self._start_time + self.duration)
      )

  def do(self, *args):
    if(not self._started):
      self.start()

    if(not self.done()):
      self.action((time.time() - self._start_time) / self.duration, *args)


class ClearEvent(Event):
  def __init__(self, clear_rumble = True, clear_color = False):
    super(ClearEvent, self).__init__(0, None)
    self.clear_rumble = clear_rumble
    self.clear_color = clear_color

    self._done = False

  def done(self):
    return self._done

  def do(self, controller, color):
    if(self.clear_rumble):
      controller.rumble = 0

    if(self.clear_color):
      controller.color = psmoveapi.RGB(*color)

    self._done = True


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

  COLOR_BAD   = (1.0, 0, 0)
  COLOR_GOOD  = (0, 1.0, 0)
  COLOR_CLEAR = (1.0, 1.0, 1.0)

  COLOR_LOSE  = COLOR_BAD
  COLOR_WIN   = COLOR_GOOD

  COLOR_TRANS_TIME   = 0.25
  COLOR_CONFIRM_TIME = 0.5
  COLOR_REJECT_TIME  = 0.5
  SERVER_TIME        = 1.0
  LOST_TIME          = 0.5
  HIT_TIME           = 0.5
  WON_RALLY_TIME     = 2.0
  OVER_TIME          = 3.0
  RESET_TIME         = 1.0

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
      print 'socketio:', args

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
      invert_color = False, invert_rumble = False, scale = 1.0,
      color_scale = 1.0, rumble_scale = 1.0, color_min = 0.0,
      rumble_min = 0.0):
    def flash(time, controller, color_rgb):
      power = (1 - math.cos(time * (2 * math.pi) * freq))/2
      power = min(1.0, max(0.0, power * scale))

      color_power = min(1.0, max(0.0, power * color_scale))
      color_power = color_power if(invert_color) else (1 - color_power)

      rumble_power = min(1.0, max(0.0, power * rumble_scale))
      rumble_power = (1 - rumble_power) if(invert_rumble) else rumble_power

      color_flash = tuple(map(lambda x: x * color_power, list(color_rgb)))

      if(color):
        controller.color = psmoveapi.RGB(*color_flash)
      if(rumble):
        controller.rumble = rumble_power

    return flash

  def generic_color_trans(self, source, target):
    def trans(time, controller, _):
      source_rgb = source
      if(source_rgb is None):
        source_rgb = self.color_choice

      target_rgb = target
      if(target_rgb is None):
        target_rgb = self.color_choice

      (sr, sg, sb) = source_rgb
      (tr, tg, tb) = target_rgb

      scale = lambda a, b: a + (b - a) * time
      color = (scale(sr, tr), scale(sg, tg), scale(sb, tb))
      controller.color = psmoveapi.RGB(*color)

    return trans

  ######################## socketio Housekeeping ###############################

  def on_sio_connect(self):
    print 'socketio: Connected'

  def on_sio_disconnect(self):
    print 'socketio: Disconnected'

  ######################### socketio Listeners #################################

  def on_sio_init_color_confirm(self):
    self.enable_swings = True

    self.state = GameState.START_WAIT
    self.state_data = {
        'events': [
            (Event(SIORacket.COLOR_CONFIRM_TIME,
                self.generic_flash(freq = 3, color_scale = 0.75)), None),
            (ClearEvent(), None)
          ]
      }
    self.print_state()

  def on_sio_init_color_reject(self):
    self.enable_swings = False

    self.state = GameState.COLOR_SELECTION
    self.state_data = {
        'events': [
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_BAD)), None),
            (Event(SIORacket.COLOR_REJECT_TIME,
                self.generic_flash()), SIORacket.COLOR_BAD),
            (ClearEvent(clear_color = True), SIORacket.COLOR_BAD),
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SIORacket.COLOR_BAD, None)), None)
          ]
      }
    self.print_state()

  def on_sio_game_is_server(self):
    self.enable_swings = True

    self.state = GameState.SERVER
    self.state_data = {
        'events': [
            (Event(SIORacket.SERVER_TIME, self.generic_flash(freq = 2)), None),
            (ClearEvent(), None)
          ]
      }
    self.print_state()

  def on_sio_game_missed_ball(self):
    self.enable_swings = True

    self.state = GameState.LOST_RALLY
    self.state_data = {
        'events': [
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_LOSE)), None),
            (Event(SIORacket.LOST_TIME,
                self.generic_flash(freq = 2)), SIORacket.COLOR_LOSE),
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SIORacket.COLOR_LOSE, None)), None),
            (ClearEvent(), None)
          ]
      }
    self.print_state()

  def on_sio_game_hit_ball(self, data):
    strength = data['strength']

    self.enable_swings = True

    self.state = GameState.HIT_BALL
    self.state_data = {
        'events': [
            (Event(SIORacket.HIT_TIME,
                self.generic_flash(scale = strength)), None),
            (ClearEvent(), None)
          ]
      }
    self.print_state()

  def on_sio_game_won_rally(self):
    self.state = GameState.WON_RALLY
    self.state_data = {
        'events': [
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_WIN)), None),
            (Event(SIORacket.WON_RALLY_TIME,
                self.generic_flash(freq = 2)), SIORacket.COLOR_WIN),
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SIORacket.COLOR_WIN, None)), None),
            (ClearEvent(), None)
          ]
      }
    self.print_state()

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
            (Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_CLEAR)), None),
            (Event(SIORacket.RESET_TIME, self.generic_flash()),
                SIORacket.COLOR_CLEAR),
            (ClearEvent(), None)
          ]
      }
    self.print_state()

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

  def print_state(self):
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

  def on_button(self, controller, buttons):
    print 'psmove:', buttons, 'pressed'

    if(psmoveapi.Button.PS in buttons):
      if(self.state == GameState.PRE_GAME):
        self.state = GameState.COLOR_SELECTION
        self.print_state()

      # elif(self.state == GameState.COLOR_SELECTION):

      elif(self.state == GameState.COLOR_WAIT):
        if(bool(random.randint(0, 1))):
          print 'self.on_sio_init_color_reject()'
          self.on_sio_init_color_reject()
        else:
          print 'self.on_sio_init_color_confirm()'
          self.on_sio_init_color_confirm()

      elif(self.state == GameState.START_WAIT):
        print 'self.on_sio_game_is_server()'
        self.on_sio_game_is_server()

      # elif(self.state == GameState.SERVER):

      elif(self.state == GameState.GAMEPLAY):
        if(bool(random.randint(0, 3))):
          print 'self.on_sio_game_hit_ball()'
          self.on_sio_game_hit_ball()
          if(bool(random.randint(0, 1))):
            print 'self.on_sio_game_won_rally()'
            self.on_sio_game_won_rally()
        else:
          print 'self.on_sio_game_missed_ball()'
          self.on_sio_game_missed_ball()

        if(not bool(random.randint(0, 5))):
          if(bool(random.randint(0, 1))):
            print 'self.on_sio_game_over()'
            self.on_sio_game_over()
          else:
            print 'self.on_sio_game_over()'
            self.on_sio_game_over()

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
      self.print_state()

  ######################### Housekeeping Events ################################

  def on_init(self, controller):
    print 'psmove:', controller, 'connected!'
    controller.color = psmoveapi.RGB(*SIORacket.COLOR_CLEAR)

  def on_leave(self, controller):
    print 'psmove:', controller, 'disconnected!'

  def on_refresh(self, controller, swing_state):
    # To be changed below
    next_state = None
    enable_swings = False

    # Here is where most of the day-to-day logic takes effect
    if(self.state == GameState.PRE_GAME
        or self.state == GameState.COLOR_SELECTION
        or self.state == GameState.COLOR_WAIT
        or self.state == GameState.START_WAIT):
      enable_swings = self.enable_swings

    else:
      if(self.state == GameState.SERVER
          or self.state == GameState.GAMEPLAY):
        next_state = GameState.GAMEPLAY
        enable_swings = True

      elif(self.state == GameState.WON_RALLY
          or self.state == GameState.LOST_RALLY):
        next_state = GameState.GAMEPLAY

      # elif(self.state == GameState.END_GAME_WIN
      #     or self.state == GameState.END_GAME_LOST):
      #   pass

    if(self.state_data is not None):
      if('events' in self.state_data):
        events = self.state_data['events']

        if(len(events) == 0):
          if(next_state is not None):
            self.state = next_state
            del self.state_data['events']
        else:
          (event, color) = events[0]
          color = self.color_choice if(color is None) else color

          event.do(controller, color)
          if(event.done()):
            events.pop(0)

      elif(len(self.state_data) == 0):
        self.state_data = None

    return enable_swings

  def exit(self):
    self.sio.disconnect()
