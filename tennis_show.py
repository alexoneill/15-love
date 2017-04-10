#!/usr/bin/python2
# tennis_show.py
# nroberts 04/10/2017

from show import Show
import random

def random_color():
    func = lambda: random.randint(0, 255) / 255.0
    return (func(), func(), func())

class TennisShow(Show):

    PLAYER1_START = 16
    PLAYER2_START = 400

    def init(self):
        self.player1 = TennisShow.Player(facing_right=True, color=random_color())
        self.player2 = TennisShow.Player(facing_right=False, color=random_color())

        # define event dispatch
        self.actions = { "swing" : TennisShow.swing }

    def update(self):
        event = self.receive_event()

        # Take action based on received event
        if event:
            name, data = event
            self.actions[name](self, data)

        # Render player swings
        self.render_swing(self.player1)
        self.render_swing(self.player2)

        self.player1.update()
        self.player2.update()

    def swing(self, data):
        if data["player"] == 1:
            self.player1.swing()
        elif data["player"] == 2:
            self.player2.swing()

    def render_swing(self, player):
        if player.is_swinging:
            x = player.get_sequence()
            fade_frames = 4 # frames
            self.bridge.set_fade(x, player.color, fade_frames)

    class Player(object):
        def __init__(self, facing_right, color):
            self.score = 0
            self.color = color
            self.facing_right = facing_right
            self.is_swinging = False

        def swing(self):
            if self.is_swinging:
                return
            self.is_swinging = True
            self.swing_progress = 0

        def update(self):
            if self.is_swinging:
                self.swing_progress += 1
                if self.swing_progress > 10:
                    self.is_swinging = False

        def get_sequence(self):
            if self.facing_right:
                return TennisShow.PLAYER1_START + self.swing_progress
            else:
                return TennisShow.PLAYER2_START - self.swing_progress
