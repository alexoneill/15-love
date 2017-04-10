#!/usr/bin/python2
# bridge.py
# nroberts 04/10/2017
# Simple high level interface keeping track of what to light up

class LightTimer(object):
    # sequence: light to light up
    # top/bottom: True/False depending on whether to light up top or bottom
    # color: original color to light the sequence
    # fade_frames: the number of frames in the lifespan of the light (None if permanent)
    def __init__(self, sequence, top, bottom, color, fade_frames):
        self.sequence = sequence
        self.top = top
        self.bottom = bottom
        self.color = color
        self.fade_frames = fade_frames

    def fade(self):
        if self.fade_frames:
            self.fade_frames -= 1

    def is_faded(self):
        return self.fade_frames != None and self.fade_frames <= 0

    def __str__(self):
        top_bot_str = "T" if self.top else ""
        top_bot_str += "B" if self.bottom else ""
        return "Light #: {}; top/bottom: {}; color: {}".format(
                 self.sequence, top_bot_str, self.color
               )

class Bridge(object):
    def __init__(self):
        self.lights = []
        self.init()

    # Fade affected frames once
    def update(self):
        for light in self.lights:
            light.fade()
        self.lights = [ timer for timer in self.lights if not timer.is_faded() ]
        self.paint()

    def set_fade(self, sequence, color, fade_frames):
        # Set both top and bottom lights to that color (hence True/False)
        timer = LightTimer(sequence, True, True, color, fade_frames)
        self.lights.append(timer)

    def init():
        """ Override me! """
        raise NotImplementedError

    def paint():
        """ Override me! """
        raise NotImplementedError
