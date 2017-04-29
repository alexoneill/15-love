# sio_racket.py
# aoneill - 04/28/17

import math
import mock
import random
import socketIO_client as sio

from libs import psmoveapi

from base import event
from base import racket
from events import clear_event


class GameState(object):
  '''
  Game states for the controller.
  '''
  COLOR_SELECTION = 0
  COLOR_WAIT = 1
  START_WAIT = 2
  SERVER = 3
  GAMEPLAY = 4
  HIT_BALL = 5
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

  # Base colors
  COLOR_BAD   = (1.0, 0, 0)
  COLOR_GOOD  = (0, 1.0, 0)
  COLOR_CLEAR = (1.0, 1.0, 1.0)

  # Colors for game outcomes
  COLOR_LOSE  = COLOR_BAD
  COLOR_WIN   = COLOR_GOOD

  # Times for animations
  COLOR_TRANS_TIME   = 0.15
  COLOR_CONFIRM_TIME = 0.5
  COLOR_REJECT_TIME  = 0.25
  SERVER_TIME        = 1.0
  HIT_TIME           = 0.5
  WON_RALLY_TIME     = 1.0
  LOST_RALLY_TIME    = 1.0
  OVER_TIME          = 5.0

  def __init__(self, sio_host, sio_port, player_num):
    super(SIORacket, self).__init__()

    # Save parameters
    self.sio_host = sio_host
    self.sio_port = sio_port
    self.player_num = player_num

    # socketio config
    # self._sio = sio.socketio(self.sio_host, self.sio_port)

    # TODO: Remove this in favor of the above
    self._sio = type('', (), {})
    def print2(*args):
      print 'socketio:', args

    # TODO: Here too
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
    self.state = GameState.COLOR_SELECTION
    self.state_data = None
    self.color_choice = None
    self.enable_swings = False

    print 'socketio: init'

  ################################ Helpers #####################################

  def generic_flash(self, freq = 1, rumble = True, color = True,
      invert_color = False, invert_rumble = False, scale = 1.0,
      color_scale = 1.0, rumble_scale = 1.0, color_min = 0.0,
      rumble_min = 0.0):
    # Generate a function which produces a 'flashing' effect on the rumble
    # colors for the controller

    def flash(time, controller, color_rgb):
      # Given a color to flash around and the controller, flash based on the
      # time argument (assumed to go from [0, 1])

      # Get base power
      power = (1 - math.cos(time * (2 * math.pi) * freq))/2
      power = min(1.0, max(0.0, power * scale))

      # Get color power
      color_power = min(1.0, max(0.0, power * color_scale))
      color_power = color_power if(invert_color) else (1 - color_power)

      # Get rumble power
      rumble_power = min(1.0, max(0.0, power * rumble_scale))
      rumble_power = (1 - rumble_power) if(invert_rumble) else rumble_power

      # Get the color
      color_flash = tuple(map(lambda x: x * color_power, list(color_rgb)))

      if(color):
        controller.color = psmoveapi.RGB(*color_flash)

      if(rumble):
        controller.rumble = rumble_power

    return flash

  def generic_color_trans(self, source, target):
    # Generate a function which produces a simple linear transition between
    # two colors

    def trans(time, controller, _):
      # If the source is None, we consider this to actually be the user-chosen
      # color (from the start)
      source_rgb = source
      if(source_rgb is None):
        source_rgb = self.color_choice

      # Similar for the target
      target_rgb = target
      if(target_rgb is None):
        target_rgb = self.color_choice

      # Unpack
      (sr, sg, sb) = source_rgb
      (tr, tg, tb) = target_rgb

      # Scale and color
      scale = lambda a, b: a + (b - a) * time
      color = (scale(sr, tr), scale(sg, tg), scale(sb, tb))
      controller.color = psmoveapi.RGB(*color)

    return trans

  ######################## socketio Housekeeping ###############################

  def on_sio_connect(self):
    # Log the connection
    print 'socketio: Connected'

  def on_sio_disconnect(self):
    # Log the drop
    print 'socketio: Disconnected'

  ######################### socketio Listeners #################################

  def on_sio_init_color_confirm(self):
    # Callback for a color confirmation event

    # Ready for swings!
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.START_WAIT
    self.state_data = {
        'events': [
            (event.Event(SIORacket.COLOR_CONFIRM_TIME,
                self.generic_flash(freq = 3, color_scale = 0.75)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  def on_sio_init_color_reject(self):
    # Callback for a color rejection event

    # Disable swings (not at the game yet)
    self.enable_swings = False

    # Parameterize the transition with animations
    self.state = GameState.COLOR_SELECTION
    self.state_data = {
        'events': [
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_BAD)), None),
            (event.Event(SIORacket.COLOR_REJECT_TIME,
                self.generic_flash()), SIORacket.COLOR_BAD),
            (clear_event.ClearEvent(clear_color = True), SIORacket.COLOR_BAD),
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SIORacket.COLOR_BAD, None)), None)
          ]
      }

  def on_sio_game_is_server(self):
    # Callback for when the player becomes the person serving the ball

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.SERVER
    self.state_data = {
        'events': [
            (event.Event(SIORacket.SERVER_TIME,
                self.generic_flash(freq = 2)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  def on_sio_game_missed_ball(self):
    # Callback for a missed ball event

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.LOST_RALLY
    self.state_data = {
        'events': [
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_LOSE)), None),
            (event.Event(SIORacket.LOST_RALLY_TIME,
                self.generic_flash(freq = 2)), SIORacket.COLOR_LOSE),
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SIORacket.COLOR_LOSE, None)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  def on_sio_game_hit_ball(self, data):
    # Callback for a hit ball event

    # Parse parameters
    strength = data['strength']

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.HIT_BALL
    self.state_data = {
        'events': [
            (event.Event(SIORacket.HIT_TIME,
                self.generic_flash(color_scale = strength)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  def on_sio_game_won_rally(self):
    # Callback for when a player wins the rally

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.WON_RALLY
    self.state_data = {
        'events': [
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SIORacket.COLOR_WIN)), None),
            (event.Event(SIORacket.WON_RALLY_TIME,
                self.generic_flash(freq = 2)), SIORacket.COLOR_WIN),
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SIORacket.COLOR_WIN, None)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  def on_sio_game_over(self, data):
    # Callback for when the game ends

    # Parse parameters
    is_winner = data['is_winner']

    # Disable swings
    self.enable_swings = False

    # Chose which color and which end-state
    color = SIORacket.COLOR_WIN
    if(is_winner):
      self.state = GameState.END_GAME_WIN
    else:
      color = SIORacket.COLOR_LOSE
      self.state = GameState.END_GAME_LOST

    # Parameterize the transition with animations
    self.state_data = {
        'events': [
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, color)), None),
            (event.Event(SIORacket.OVER_TIME,
                self.generic_flash(freq = 5)), color),
            (event.Event(SIORacket.COLOR_TRANS_TIME,
                self.generic_color_trans(color, SIORacket.COLOR_CLEAR)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  ########################### socketio Emits ###################################

  def sio_init_color_choice(self, color):
    # Method to communicate the color choice
    self._sio.emit('init_color_choice', {
        'color': color
      })

  def sio_game_swing(self, hand, strength):
    # Method to communicate the swing event

    self._sio.emit('init_color_choice', {
        'player_num': self.player_num,
        'hand': (0 if(hand == racket.Handedness.LEFT) else 1),
        'strength': strength
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
    # Method to parse button presses

    # Temporary to cycle through animations
    # Pressing the PS button simulates an in-order server event
    if(psmoveapi.Button.PS in buttons):
      if(self.state == GameState.COLOR_WAIT):
        if(bool(random.randint(0, 1))):
          self.on_sio_init_color_reject()
        else:
          self.on_sio_init_color_confirm()

      elif(self.state == GameState.START_WAIT):
        self.on_sio_game_is_server()

      elif(self.state == GameState.GAMEPLAY):
        end_rally = False

        if(bool(random.randint(0, 3))):
          self.on_sio_game_hit_ball({'strength': 0.75})
          if(not bool(random.randint(0, 5))):
            self.on_sio_game_won_rally()
            end_rally = True
        else:
          self.on_sio_game_missed_ball()
          end_rally = True

        if(end_rally and not bool(random.randint(0, 5))):
          if(bool(random.randint(0, 1))):
            self.on_sio_game_over({'is_winner': False})
          else:
            self.on_sio_game_over({'is_winner': True})

      return

    # Color choosing logic
    if(self.state == GameState.COLOR_SELECTION):
      choices = (psmoveapi.Button.SQUARE, psmoveapi.Button.TRIANGLE,
        psmoveapi.Button.CROSS, psmoveapi.Button.CIRCLE)

      print 'psmove:', buttons, 'pressed'

      # Cycle through button options
      for button in choices:
        if(button in buttons):
          self.color_choice = SIORacket.COLORS[button]
          controller.color = psmoveapi.RGB(*self.color_choice)
          return

    # Color confirmation logic
    if((self.color_choice is not None) and (psmoveapi.Button.MOVE in buttons)):
      self.sio_init_color_choice(self.color_choice)
      self.state = GameState.COLOR_WAIT

  ######################### Housekeeping Events ################################

  def on_init(self, controller):
    # Method for initialization
    print 'psmove:', controller, 'connected!'

    # Set the controller to be blank
    controller.color = psmoveapi.RGB(*SIORacket.COLOR_CLEAR)
    controller.rumble = 0

  def on_leave(self, controller):
    # Method for when a controller is dropped
    print 'psmove:', controller, 'disconnected!'

  def on_refresh(self, controller, swing_state):
    # To be changed below
    next_state = None
    enable_swings = False

    # Do nothing special if we are in the color selection / confirmation stage
    if(self.state == GameState.COLOR_SELECTION
        or self.state == GameState.COLOR_WAIT
        or self.state == GameState.START_WAIT):
      enable_swings = self.enable_swings

    else:
      # The following should allow swings and transition back to GAMEPLAY
      if(self.state == GameState.SERVER
          or self.state == GameState.GAMEPLAY
          or self.state == GameState.HIT_BALL):
        next_state = GameState.GAMEPLAY
        enable_swings = True

      # These should also transition to GAMEPLAY, but without swings
      elif(self.state == GameState.WON_RALLY
          or self.state == GameState.LOST_RALLY):
        next_state = GameState.GAMEPLAY

      # These should make the game end
      elif(self.state == GameState.END_GAME_WIN
          or self.state == GameState.END_GAME_LOST):
        next_state = GameState.COLOR_SELECTION
        enable_swings = False

    # Work through pending animations
    if(self.state_data is not None):
      if('events' in self.state_data):
        events = self.state_data['events']

        # Remove events if there are none left
        if(len(events) == 0):
          if(next_state is not None):
            self.state = next_state
            del self.state_data['events']

        else:
          # Execute the event at the front of the queue
          (event, color) = events[0]
          color = self.color_choice if(color is None) else color

          event.do(controller, color)
          if(event.done()):
            events.pop(0)

      # Clean up the state data if no more exists
      elif(len(self.state_data) == 0):
        self.state_data = None

    return enable_swings

  def exit(self):
    # Clean-up method
    self.sio.disconnect()
