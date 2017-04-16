#!/usr/bin/python2
# tennis_show.py
# nroberts 04/10/2017

from show import Show
from bridge import Bridge
import random

# print diagnostic information for unrecognized event
def unrecognized_event(name):
    def print_error(data):
        print "Unrecognized event. Name: {}, Data: {}".format(name, data)
    return print_error

def sign(x):
    return 1 if x > 0 else -1

def random_color():
    func = lambda: random.randint(0, 255) / 255.0
    return (func(), func(), func())

class TennisShow(Show):

    def init(self):
        # offset of start panel for player 1 and player 2
        p1_seq = Bridge.SEQ_LO
        p2_seq = Bridge.SEQ_HI

        # ball comes in front of players
        player_priority = 3
        ball_priority = 4

        p1_color = random_color()
        p2_color = random_color()
        ball_color = random_color()

        # how long to make the swing
        max_swing = 20 # sequences

        p1 = Player(color=p1_color, origin=p1_seq, max_swing=max_swing,
                velocity=1, priority=player_priority)
        p2 = Player(color=p2_color, origin=p2_seq, max_swing=max_swing,
                velocity=-1, priority=player_priority)
        ball = Ball(color=ball_color, origin=p1_seq, max_seq=p2_seq,
                velocity=3, priority=ball_priority)

        # player 1 serves first
        p1.serving = True

        # define what objects game should update every loop
        self.moving_objects = [ p1, p2, ball ]

        # set up instance variables
        self.p1, self.p2, self.ball = p1, p2, ball

        # define what functions we enter at the start
        self.actions = { self.start_show }

        # scores for player 1 and player 2
        self.scores = { 1 : 0, 2 : 0 }

    """**********************************************************************************
    *   What the update does:                                                           *
    *   (1) receives an event from the queue                                            *
    *   (2) acts on the event if it was received, by the event dispatch                 *
    *   (3) calls each "action" exactly once. Note that actinos should run quickly, as  *
    *       they'll be called 40 times/second. The members of self.actions are actions  *
    *       that should run every time update is called.                                *
    **********************************************************************************"""
    def update(self):
        event = self.receive_event()

        # do all the current animations
        for action in self.actions:
            action(event)

    """**************************************************************
    *  The start of the show performs a brief light show. When the  *
    *  light show ends, the game loop starts with player 1 serving. *
    **************************************************************"""
    def start_show(self, event):
        # TODO: Indicate where players should stand, have players select color?
        print "Showing start show"
        if event:
            name, data = event
            # currently, there's nothing we do in the start show, but this could change.
            { }.get(name, unrecognized_event(name))(data)

        # Don't have a start show yet, so just start the game loop
        self.actions.remove(self.start_show)
        self.actions.add(self.game_loop)

    """****************************************************************
    *  In the game loop, we render the balls and player swings, check *
    *  for hits, and tell the balls and the players to update.        *
    ****************************************************************"""
    def game_loop(self, event):
        if event:
            name, data = event
            # Python's version of a switch statement? It's event dispatch
            { "swing" : self.swing }.get(name, unrecognized_event(name))(data)

        fade_frames = 4 #frames
        for obj in self.moving_objects:
          obj.render(self.bridge, fade_frames)

        # check for hitting the ball
        self.check_for_hit(self.p1)
        self.check_for_hit(self.p2)

        # Update game objects
        for obj in self.moving_objects:
            obj.update(self)

    # swing event received
    def swing(self, data):
        def player_swing(player, opponent):
            player.swing()
            ball = self.ball
            # serve if it is your turn to serve
            if player.serving and not ball.is_active:
                player.serve(ball)
                opponent.serving = True
                player.serving = False

        if data["player"] == 1:
            player_swing(self.p1, opponent=self.p2)
        elif data["player"] == 2:
            player_swing(self.p2, opponent=self.p1)

    def check_for_hit(self, player):
        ball = self.ball
        if player.is_active and ball.is_active:
            pseq = player.get_seq()
            bseq = ball.get_seq()

            # hit ball if it has crossed where the player is swinging
            if player.velocity > 0 and ball.velocity < 0 and bseq <= pseq:
                ball.hit()
            elif player.velocity < 0 and ball.velocity > 0 and bseq >= pseq:
                ball.hit()

    # Award points to a player
    def on_missed_ball(self, awarded_player):
        self.scores[awarded_player] += 1

        # TODO: Engulf entire bridge in red after a missed point
        # TODO: Display score in some way on the bridge

        # Player wins after getting 4 points. This is the way of tennis.
        if self.scores[awarded_player] == 4:
            self.actions.remove(self.game_loop)
            self.actions.add(self.firework_show)

    # Show a show at the end for the winning player (eventually)
    def firework_show(self, _):
        winning_player = 1 if self.scores[1] == 4 else 2 # decide which player won
        # TODO: Make a fun firework show at the end. Maybe design in Lumiverse??
        self.running = False # just end the show for now
        print "Showing fireworks"

# Common abstract class for objects with location, color, starting point, and velocity
class MovingObject(object):
    def __init__(self, origin, color, velocity, priority, **kwargs):
        self.color = color
        self.origin = origin
        self.x = None # offset from origin, in sequences
        self.velocity = velocity
        self.priority = priority
        self.is_active = False
        self.init(**kwargs)

    def init(self):
        """ Override me! """
        raise NotImplementedError

    def update(self):
        """ Override me! """
        raise NotImplementedError

    def render(self, bridge, fade_frames):
        if self.is_active:
            seq = self.get_seq()
            prev_seq = int(self.origin + self.x - self.velocity)

            # also light up the panels that were skipped in last velocity update
            for i in xrange(seq, prev_seq, -sign(self.velocity)):
                bridge.set_fade(i, self.color, fade_frames, self.priority)

    # returns current sequence
    def get_seq(self):
        return int(self.origin + self.x)

# Class that represents ball state, including velocity and location
class Ball(MovingObject):
    # max_seq is the furthest sequence the ball is allowed to go to
    def init(self, max_seq):
        self.max_range = max_seq - self.origin
        self.x = 0
        self.starting_velocity = self.velocity

    def update(self, show):
        if self.is_active:
            self.x += self.velocity
            if self.x < 0 or self.x > self.max_range:
                self.is_active = False

                # player who got the point
                awarded_player = 2 if self.x < 0 else 1
                show.on_missed_ball(awarded_player)

    def hit(self):
        # change direction when hit
        self.velocity = -self.velocity

# Class that represents where the player's state, including swing location
class Player(MovingObject):
    def init(self, max_swing):
        self.score = 0
        self.max_swing = max_swing # number of panels the swing spans
        self.serving = False

    def swing(self):
        if self.is_active:
            return
        self.is_active = True
        self.x = 0

    def serve(self, ball):
        # set ball to active with new velocity
        ball.velocity = ball.starting_velocity * self.velocity
        ball.x = 0 if ball.velocity > 0 else ball.max_range
        ball.is_active = True

    def update(self, show):
        if self.is_active:
            # advance swing in positive or negative direction
            self.x += self.velocity

            # check if the swing is in the right range
            if abs(self.x) >= self.max_swing:
                self.is_active = False
