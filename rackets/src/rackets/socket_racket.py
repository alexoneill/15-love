# sio_racket.py
# aoneill - 04/28/17

import math
import functools

import socket
import threading
import Queue
import pickle

from libs import psmoveapi

from src.base import event
from src.base import racket
from src.events import clear_event


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



def filter_player(func):
  @functools.wraps(func)
  def inner(self, data):
    if(('player_num' in data) and (data['player_num'] == self.player_num)):
      del data['player_num']
      if(len(data) > 0):
        func(self, data)
      else:
        func(self)

  return inner


class EventListener(threading.Thread):
  MSG_LEN = 4096

  def __init__(self, sock):
    super(EventListener, self).__init__()

    self.sock = sock
    self._queue = Queue.Queue()

    self.start()

  def has(self):
    return (not self._queue.empty())

  def get(self, blocking = False):
    return self._queue.get(blocking)

  def run(self):
    while(True):
      data = self.sock.recv(EventListener.MSG_LEN)
      if(data == ''):
        return

      data = pickle.loads(data)
      print 'EventListener:', data
      self._queue.put(data)


class EventDispatcher(threading.Thread):
  def __init__(self, sock):
    super(EventDispatcher, self).__init__()
    self._listener = EventListener(sock)
    self._events = {}

    self.start()

  def on(self, event, func):
    self._events[event] = func

  def run(self):
    while(True):
      (id_str, data) = self._listener.get(blocking = True)
      if(id_str in self._events):
        func = self._events[id_str]

        print 'EventDispatcher:', (func.__name__, data)
        func(data)


class EventSender(threading.Thread):
  MSG_LEN = 4096

  def __init__(self, sock):
    super(EventSender, self).__init__()

    self.sock = sock
    self._queue = Queue.Queue()

    self.start()

  def put(self, data):
    return self._queue.put(data)

  def run(self):
    while(True):
      data = self._queue.get(True)
      print 'EventSender:', data

      data = pickle.dumps(data)
      self.sock.send(data)


class SocketRacket(racket.Racket):
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
  COLOR_TRANS_TIME   = 0.2
  COLOR_WAIT_TIME    = 0.1
  COLOR_CONFIRM_TIME = 0.5
  COLOR_REJECT_TIME  = 0.25
  SERVER_TIME        = 1.0
  HIT_TIME           = 0.5
  WON_RALLY_TIME     = 1.0
  LOST_RALLY_TIME    = 1.0
  OVER_TIME          = 5.0

  def __init__(self, sio_host, sio_port, player_num):
    super(SocketRacket, self).__init__()

    # Save parameters
    self.sio_host = sio_host
    self.sio_port = sio_port
    self.player_num = player_num

    # socketio config
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((self.sio_host, self.sio_port))

    # Get event helpers
    self._ev_disp = EventDispatcher(sock)
    self._ev_send = EventSender(sock)

    # socketio callbacks
    # Basic
    self._ev_disp.on('connect', self.on_sio_connect)
    self._ev_disp.on('disconnect', self.on_sio_disconnect)

    # Game-based - Listening
    self._ev_disp.on('init_color_reject', self.on_sio_init_color_reject)
    self._ev_disp.on('init_color_confirm', self.on_sio_init_color_confirm)
    self._ev_disp.on('game_is_server', self.on_sio_game_is_server)
    self._ev_disp.on('game_missed_ball', self.on_sio_game_missed_ball)
    self._ev_disp.on('game_hit_ball', self.on_sio_game_hit_ball)
    self._ev_disp.on('game_won_rally', self.on_sio_game_won_rally)
    self._ev_disp.on('game_over', self.on_sio_game_over)
    self._ev_disp.on('game_restart', self.on_sio_game_restart)

    print 'socketio: init'

    # Other parameters
    self.state = GameState.COLOR_SELECTION
    self.state_data = None
    self.color_choice = None
    self.enable_swings = False

    print 'racket: init'

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

  @filter_player
  def on_sio_init_color_confirm(self):
    # Callback for a color confirmation event
    print 'socketio: init_color_confirm'

    # Ready for swings!
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.START_WAIT
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.COLOR_CONFIRM_TIME,
                self.generic_flash(freq = 3, color_scale = 0.75)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  @filter_player
  def on_sio_init_color_reject(self):
    # Callback for a color rejection event
    print 'socketio: init_color_reject'

    # Disable swings (not at the game yet)
    self.enable_swings = False

    # Parameterize the transition with animations
    self.state = GameState.COLOR_SELECTION
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SocketRacket.COLOR_BAD)), None),
            (event.Event(SocketRacket.COLOR_REJECT_TIME,
                self.generic_flash()), SocketRacket.COLOR_BAD),
            (clear_event.ClearEvent(clear_color = True), SocketRacket.COLOR_BAD),
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SocketRacket.COLOR_BAD, None)), None)
          ]
      }

  @filter_player
  def on_sio_game_is_server(self):
    # Callback for when the player becomes the person serving the ball
    print 'socketio: game_is_server'

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.SERVER
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.SERVER_TIME,
                self.generic_flash(freq = 2)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  @filter_player
  def on_sio_game_missed_ball(self):
    # Callback for a missed ball event
    print 'socketio: game_missed_ball'

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.LOST_RALLY
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SocketRacket.COLOR_LOSE)), None),
            (event.Event(SocketRacket.LOST_RALLY_TIME,
                self.generic_flash(freq = 2)), SocketRacket.COLOR_LOSE),
            (clear_event.ClearEvent(clear_color = True), SocketRacket.COLOR_LOSE),
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SocketRacket.COLOR_LOSE, None)), None)
          ]
      }

  @filter_player
  def on_sio_game_hit_ball(self, data):
    # Callback for a hit ball event
    print 'socketio: game_hit_ball'

    # Parse parameters
    strength = data['strength']

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.HIT_BALL
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.HIT_TIME,
                self.generic_flash(color_scale = strength)), None),
            (clear_event.ClearEvent(), None)
          ]
      }

  @filter_player
  def on_sio_game_won_rally(self):
    # Callback for when a player wins the rally
    print 'socketio: game_won_rally'

    # Keep swings enabled
    self.enable_swings = True

    # Parameterize the transition with animations
    self.state = GameState.WON_RALLY
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SocketRacket.COLOR_WIN)), None),
            (event.Event(SocketRacket.WON_RALLY_TIME,
                self.generic_flash(freq = 2)), SocketRacket.COLOR_WIN),
            (clear_event.ClearEvent(clear_color = True), SocketRacket.COLOR_WIN),
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(SocketRacket.COLOR_WIN, None)), None),
          ]
      }

  @filter_player
  def on_sio_game_over(self, data):
    # Callback for when the game ends
    print 'socketio: game_over'

    # Parse parameters
    winner = data['winner']

    # Disable swings
    self.enable_swings = False

    # Chose which color and which end-state
    color = SocketRacket.COLOR_WIN
    if(self.player_num == winner):
      self.state = GameState.END_GAME_WIN
    else:
      color = SocketRacket.COLOR_LOSE
      self.state = GameState.END_GAME_LOST

    # Parameterize the transition with animations
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, color)), None),
            (event.Event(SocketRacket.OVER_TIME,
                self.generic_flash(freq = 5)), color),
            (clear_event.ClearEvent(clear_color = True), color),
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(color, SocketRacket.COLOR_CLEAR)), None)
          ]
      }

  def on_sio_game_restart(self):
    # Callback for when the game ends
    print 'socketio: game_restart'

    # Disable swings
    self.enable_swings = False

    # Restart the state machine
    self.state = GameState.COLOR_SELECTION

    # Parameterize the transition with animations
    self.state_data = {
        'events': [
            (event.Event(SocketRacket.OVER_TIME,
                self.generic_flash(color = False)), None),
            (event.Event(SocketRacket.COLOR_TRANS_TIME,
                self.generic_color_trans(None, SocketRacket.COLOR_CLEAR)), None)
            (clear_event.ClearEvent(clear_color = True), color),
          ]
      }

  ########################### socketio Emits ###################################

  def sio_game_reset(self):
    # Method to communicate the color choice
    self._ev_send.put(('game_reset', {}))

  def sio_init_color_choice(self, color):
    # Method to communicate the color choice
    self._ev_send.put(('init_color_choice', {
        'player_num': self.player_num,
        'color': color,
      }))

  def sio_game_swing(self, hand, strength):
    # Method to communicate the swing event

    self._ev_send.put(('game_swing', {
        'player_num': self.player_num,
        'hand': (0 if(hand == racket.Handedness.LEFT) else 1),
        'strength': strength
      }))

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

    # Forceful reset
    if((psmoveapi.Button.SELECT in buttons)
        and (psmoveapi.Button.START in buttons)):
      self.sio_game_reset()

    # Color choosing logic
    if(self.state == GameState.COLOR_SELECTION):
      choices = (psmoveapi.Button.SQUARE, psmoveapi.Button.TRIANGLE,
        psmoveapi.Button.CROSS, psmoveapi.Button.CIRCLE)

      # Cycle through button options
      for button in choices:
        if(button in buttons):
          self.color_choice = SocketRacket.COLORS[button]
          controller.color = psmoveapi.RGB(*self.color_choice)
          return

      # Color confirmation logic
      if((self.color_choice is not None) and (psmoveapi.Button.MOVE in buttons)):
        self.sio_init_color_choice(self.color_choice)

        # Signal a transition to the next state
        self.state = GameState.COLOR_WAIT
        self.state_data = {
            'events': [
                (event.Event(SocketRacket.COLOR_WAIT_TIME,
                    self.generic_flash(rumble_scale = 0.75,
                        color_scale = 0.75)), None),
                (clear_event.ClearEvent(), None)
              ]
          }

  ######################### Housekeeping Events ################################

  def on_init(self, controller):
    # Method for initialization
    print 'psmove:', controller, 'connected!'

    # Set the controller to be blank
    controller.color = psmoveapi.RGB(*SocketRacket.COLOR_CLEAR)
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
