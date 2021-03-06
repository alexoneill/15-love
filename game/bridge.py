#!/usr/bin/python2
# bridge.py
# nroberts 04/10/2017
# Simple high level interface keeping track of what to light up
from colors import Colors

class LightTimer(object):
    # sequence: light to light up
    # top/bot: True/False depending on whether to light up top or bottom
    # color: original color to light the sequence
    # fade_frames: the number of frames in the lifespan of the light (None if permanent)
    def __init__(self, sequence, top, bot, color, fade_frames):
        self.sequence = sequence
        self.top = top
        self.bot = bot
        self.color = color
        self.fade_frames = fade_frames
        self.just_inserted = True

    def fade(self):
        # don't fade the first time we're inserted
        if self.just_inserted and self.fade_frames > 0:
            self.just_inserted = False
            return
        if isinstance(self.fade_frames, int):
            self.fade_frames -= 1
            # fade by halving distance to 255 for r, g, and b
            self.color = Colors.fade(self.color, 0.95)
            if self.fade_frames == 0:
                # then we have to send a clear command
                self.color = 0, 0, 0

    def is_faded(self):
        return self.fade_frames != None and self.fade_frames < 0

    def __str__(self):
        top_bot_str = "T" if self.top else ""
        top_bot_str += "B" if self.bot else ""
        r, g, b = self.color
        return "sequence: %d; top/bot: %s; color: %0.3f, %0.3f, %0.3f" % (
                 self.sequence, top_bot_str, r, g, b
               )

class Bridge(object):

    # limits for what values sequence can be
    SEQ_HI = 195
    SEQ_LO = 1

    def __init__(self):
        # store sequence : list of timers at that position
        self.timers = {}
        self.init()

    # Fade affected timers once
    def update(self):
        for k in self.timers.keys():
            for timer, __ in self.timers[k]:
                timer.fade()

            # remove faded timers, decrease priority
            timers = [ (t, 0.9 * p) for t, p in self.timers[k] if not t.is_faded() ]
            if timers:
                self.timers[k] = timers
            else:
                del self.timers[k]

        self.paint()

    def set_fade(self, sequence, color, fade_frames, priority):
        # Set both top and bottom lights to that color (hence True/False)
        timer = LightTimer(sequence, True, True, color, fade_frames)
        self.add(sequence, (timer, priority))

    def set_on(self, sequence, color, priority):
        # set both top and bottom lights to that color, with no timeout
        timer = LightTimer(sequence, True, True, color, None)
        self.add(sequence, (timer, priority))

    def set_off(self, sequence):
        self.timers[sequence] = []

    def clear(self):
        self.timers = {}

    def add(self, key, value):
        if key > Bridge.SEQ_HI or key < Bridge.SEQ_LO: # Disallow out-of-range lights
            return
        try:
            self.timers[key].append(value)
        except KeyError:
            self.timers[key] = [value]

    # Calculates what colors to display at each light, taking weighted average
    def lights(self):
        for sequence, timers in self.timers.iteritems():
            if len(timers) == 1:
                yield timers[0][0]
            else:
                max_priority = 0
                max = None
                # count r, g, and b values on top and bottom
                for timer, priority in timers:
                    if priority > max_priority:
                        max = timer
                        max_priority = priority
                yield max

    def init(self):
        """ Override me! """
        raise NotImplementedError

    def paint(self):
        """ Override me! """
        raise NotImplementedError
