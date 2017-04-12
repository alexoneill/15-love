#!/usr/bin/python2
# tennis_show.py
# nroberts 04/10/2017

from show import Show
import random

def random_color():
    func = lambda: random.randint(0, 255) / 255.0
    return (func(), func(), func())

class TennisShow(Show):

    def init(self):
        # offset of start panel for player 1 and player 2
        p1_seq = 16
        p2_seq = 400

        p1_color = random_color()
        p2_color = random_color()
        ball_color = random_color()

        # how long to make the swing
        max_swing = 20 # sequences

        self.p1 = Player(color=p1_color, origin=p1_seq, max_swing=max_swing)
        self.p2 = Player(color=p2_color, origin=p2_seq, max_swing=max_swing)
        self.ball = Ball(color=ball_color, origin=p1_seq, extreme=p2_seq)

        # define event dispatch
        self.actions = { "swing" : self.swing }

    def update(self):
        event = self.receive_event()

        # Take action based on received event
        if event:
            name, data = event
            self.actions[name](data)

        # Render player swings
        self.render_swing(self.p1)
        self.render_swing(self.p2)

        # Render the ball
        self.render_ball(self.ball)

        self.p1.update()
        self.p2.update()
        self.ball.update()

    def swing(self, data):
        if data["player"] == 1:
            self.p1.swing()
        elif data["player"] == 2:
            self.p2.swing()

    def render_swing(self, player):
        if player.is_swinging:
            x = player.get_seq()
            fade_frames = 4 # frames
            self.bridge.set_fade(x, player.color, fade_frames)

    def render_ball(self, ball):
        if ball.in_play:
            x = ball.get_seq()
            fade_frames = 4 # frames
            self.bridge_set_fade(x, ball.color, fade_frames)

class GameObject(object):

    def __init__(self, origin, color, **kwargs):
        self.color = color
        self.origin = origin
        self.x = None # offset from origin, in sequences
        self.init(**kwargs)

    def init(self):
        """ Override me! """
        raise NotImplementedError

    def update(self):
        """ Override me! """
        raise NotImplementedError

    # returns current sequence number based on how far between lo and hi
    def get_seq(self):
        return int(self.origin + self.x)

class Ball(GameObject):
    # extreme is the furthest sequence the ball is allowed to go to
    def init(self, extreme):
        self.max_range = extreme - self.origin
        self.in_play = False
        self.x = 0
        self.v = 1 # sequence per frame

    def update(self):
        if self.in_play:
            self.x += self.v
            if self.x < 0 or self.x > self.max_range:
                self.in_play = False

class Player(GameObject):
    def init(self, max_swing):
        self.score = 0
        self.max_swing = abs(max_swing)
        self.facing_right = max_swing > 0
        self.is_swinging = False

    def swing(self):
        if self.is_swinging:
            return
        self.is_swinging = True
        self.x = 0

    def update(self):
        if self.is_swinging:
            # advance swing in positive or negative direction
            if self.facing_right:
                self.x += 1 # sequence per frame
            else:
                self.x -= 1 # sequence per frame

            # check if the swing is in the right range
            if abs(self.x) >= self.max_swing:
                self.is_swinging = False
