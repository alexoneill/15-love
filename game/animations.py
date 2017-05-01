#!/usr/bin/python2
# animations.py
# nroberts 04/16/2017

from __future__ import division
from bridge import Bridge
from colors import Colors
import random

BALL_PRIORITY = 3
PLAYER_PRIORITY = 4
ANIMATION_PRIORITY = 5
SCORE_PRIORITY = 100

# 1 if positive, -1 if negative
def sign(x):
    return 1 if x > 0 else -1

# Common abstract class for objects with location, color, starting point, and velocity
class Animation(object):
    def __init__(self, origin, color, velocity, **kwargs):
        self.color = color
        self.origin = origin
        self.x = origin # current sequence
        self.velocity = velocity
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
            prev_seq = int(self.x - self.velocity)

            # if not moving, just light up current panel
            if self.velocity == 0:
                bridge.set_fade(seq, self.color, fade_frames, self.priority)
            else:
                # also light up the panels that were skipped in last velocity update
                for i in xrange(seq, prev_seq, -sign(self.velocity)):
                    bridge.set_fade(i, self.color, fade_frames, self.priority)

    # returns current sequence
    def get_seq(self):
        return int(self.x)

# Bars for displaying score to each other
class ScoreBars(Animation):
    FADE_FRAMES = 160 # how long to hang at the end
    FLASH_CYCLE = 40 # how long to fade in and out

    def init(self, end_seq):
        self.end_x = end_seq
        print "End: ", end_seq
        self.is_active = True
        self.priority = SCORE_PRIORITY
        self.flashing = False
        self.start_color = self.color

    def update(self):
        self.x += self.velocity

        # it has reached its spot, so stop it
        if ((self.velocity < 0 and self.x <= self.end_x)
         or (self.velocity > 0 and self.x >= self.end_x)):
            self.x = self.end_x
            self.velocity = 0
            self.frames_till_end = ScoreBars.FADE_FRAMES

        # run until dead
        if self.velocity == 0:
            # die
            if self.frames_till_end == 0:
                self.is_active = False

            if self.flashing:
                adj = self.frames_till_end % ScoreBars.FLASH_CYCLE
                scale = abs(adj - ScoreBars.FLASH_CYCLE / 2)
                # shift back up by a factor of 2 since we scaled down in the previous step
                frac = 2 * scale / ScoreBars.FLASH_CYCLE
                self.color = Colors.fade(self.start_color, frac)

            self.frames_till_end -= 1

# Transitions between colors
class TransitionAnimation(object):
    def __init__(self, start, end, color):
        self.color = color
        self.next_color = color
        self.start = start
        self.end = end
        self.is_active = True

    def update(self):
        # weight current color more than next color
        self.color = Colors.weighted_avg(self.color, self.next_color, 100, 1)

    def render(self, bridge):
        for i in xrange(self.start, self.end+1): # inclusive
            bridge.set_fade(i, self.color, 1, ANIMATION_PRIORITY) # 1 frame

# Have section of bridge pulse
class PulseAnimation(object):
    FADE_TIME = 40 # 1 second
    def __init__(self, start, end, color=Colors.WHITE):
        self.fade_level = 0
        self.start_seq = start
        self.end_seq = end
        self.fading_in = True
        self.color = color
        self.is_active = True # need this to be an animation

    def update(self, color=None):
        # update color if set
        if color: self.color = color

        if self.fading_in: self.fade_level += 1
        else:              self.fade_level -= 1

        # switch direction of fade
        if self.fade_level == PulseAnimation.FADE_TIME:
            self.fading_in = False
        if self.fade_level == 0:
            self.fading_in = True

    def render(self, bridge):
        for i in xrange(self.start_seq, self.end_seq+1): #inclusive
            frac = self.fade_level / PulseAnimation.FADE_TIME # python3 division
            # fade color appropriately
            color = Colors.fade(self.color, frac)
            bridge.set_fade(i, color, 1, ANIMATION_PRIORITY) # 1 frame

# Class for the pulse animation after someone scores
# Also displays score for each player
class ScoreAnimation(object):

    # distance between consecutive score panels
    SEPARATION = 4 # sequences
    VELOCITY = 4 # sequences per frame for score bars
    FADE_FRAMES = 10 # how long it takes to fade

    def __init__(self, p1, p2, color, awarded_player):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.awarded_player = awarded_player # player number

        # start animation immediately
        self.state = "pulse" # pulse is where we make the whole bridge the same color
        self.pulse_frames = 60
        self.is_active = True

    def update(self):
        if self.pulse_frames > 0:
            self.pulse_frames -= 1

    def make_scorebar_animations(self):
        animations = []
        p1, p2 = self.p1, self.p2
        p1_offset = 26 # edge of 4-panel
        p2_offset = 185 # edge of 4-panel

        # constants used when creating animations
        v = ScoreAnimation.VELOCITY
        hi = Bridge.SEQ_HI
        lo = Bridge.SEQ_LO

        # make animations for p1 score
        for i in xrange(0, self.p1.score):
            # origin is +/- 1 so both the p1 and p2 scores display
            s1 = ScoreBars(origin=hi-1, end_seq=p1_offset, color=self.p1.color, velocity=-v)
            s2 = ScoreBars(origin=lo+1, end_seq=p2_offset, color=self.p1.color, velocity=v)

            # make most recently-earned point flash
            if self.awarded_player == 1 and i == self.p1.score - 1:
                s1.flashing = True
                s2.flashing = True

            animations.append(s1)
            animations.append(s2)
            p1_offset += ScoreAnimation.SEPARATION
            p2_offset -= ScoreAnimation.SEPARATION

        # make animations for p2 score
        for i in xrange(0, self.p2.score):
            s1 = ScoreBars(origin=hi, end_seq=p1_offset, color=self.p2.color, velocity=-v)
            s2 = ScoreBars(origin=lo, end_seq=p2_offset, color=self.p2.color, velocity=v)

            # make most recently-earned point flash
            if self.awarded_player == 2 and i == self.p2.score - 1:
                s1.flashing = True
                s2.flashing = True

            animations.append(s1)
            animations.append(s2)
            p1_offset += ScoreAnimation.SEPARATION
            p2_offset -= ScoreAnimation.SEPARATION

        return animations

    # override
    def render(self, bridge):
        if self.state == "pulse":
            for i in xrange(Bridge.SEQ_LO, Bridge.SEQ_HI+1):
                bridge.set_fade(i, self.color, self.pulse_frames, SCORE_PRIORITY)

            # display score now
            self.state = "score"

        # create scoreboard animations
        elif self.state == "score":
            if self.pulse_frames > 0:
                self.pulse_frames -= 1
            else:
                print "Spawning score animations"
                self.animations = self.make_scorebar_animations()
                self.state = "moving_score"

        # delegate to animations
        elif self.state == "moving_score":
            any_active = False

            # delegate rendering/updating to scoreboard animations
            for animation in self.animations:
                if animation.is_active:
                    any_active = True
                    animation.render(bridge, ScoreAnimation.FADE_FRAMES)
                    animation.update()

            # whole score animation ends when all individual animations are done
            if not any_active:
                self.is_active = False

# Class that represents ball state, including velocity and location
class Ball(Animation):
    INCREASE = 1.05 # multiplicative increase of ball speed
    # max_seq is the furthest sequence the ball is allowed to go to
    def init(self, max_seq):
        self.max_seq = max_seq
        self.starting_velocity = self.velocity
        self.priority = BALL_PRIORITY
        self.counter = 1.0

    def update(self, show):
        if self.is_active:
            self.x += self.velocity
            if self.x < self.origin or self.x > self.max_seq:
                print "Ball has been missed at location %d" % self.x
                self.is_active = False

                # player who got the point
                awarded_player = 2 if self.x <= 50 else 1

                # make the show perform the actions it does when a player misses
                show.on_missed_ball(awarded_player)

    def hit(self, player):
        # change direction when hit
        if self.velocity == 0:
            self.velocity = self.starting_velocity * sign(player.velocity) * player.strength
        else:
            self.counter *= Ball.INCREASE
            self.velocity = self.counter * sign(player.velocity) * self.starting_velocity * player.strength



# Class that represents where the player's state, including swing location
class Player(Animation):
    def init(self, max_swing):
        self.score = 0
        self.max_swing = max_swing # number of panels the swing spans
        self.serving = False
        self.priority = PLAYER_PRIORITY
        self.score = 0

    def swing(self):
        if self.is_active:
            return
        self.is_active = True
        self.x = self.origin

    def set_strength(self, strength):
        self.strength = strength
        multiplier = 2 * sign(self.velocity)
        self.velocity = multiplier * strength

    def update(self, show):
        if self.is_active:
            # advance swing in positive or negative direction
            self.x += self.velocity

            # check if the swing is in the right range
            if abs(self.x - self.origin) > self.max_swing:
                print "Player done swinging at %d" % self.x
                self.is_active = False

# firework show
class FireworkBurst(Animation):
    def init(self, priority):
        self.is_active = True
        self.priority = priority

    def update(self):
        self.x += self.velocity
        if self.x > Bridge.SEQ_HI or self.x < Bridge.SEQ_LO:
            self.is_active = False

class FireworkAnimation(object):
    MAX_VELOCITY = 6
    MIN_VELOCITY = 2
    FADE_FRAMES = 40
    def __init__(self, color):
        self.is_active = True # always active

        p = random.random() # priority (and vividness)
        color = Colors.fade(color, p)
        seq = random.randint(Bridge.SEQ_LO, Bridge.SEQ_HI)
        v = random.random() * (FireworkAnimation.MAX_VELOCITY - FireworkAnimation.MIN_VELOCITY)
        v += FireworkAnimation.MIN_VELOCITY

        lo, hi = 10, 30
        pr = p * (hi - lo) + lo # choose random number in range [lo, hi) for priority

        # create two bursts going in opposite directions
        self.animations = [
            FireworkBurst(origin=seq, color=color, velocity=v, priority=pr),
            FireworkBurst(origin=seq, color=color, velocity=-v, priority=pr),
        ]

    # delegate updating and rendering to underlying animations
    def update(self):
        for a in self.animations:
            a.update()
        self.is_active = any(map(lambda a: a.is_active, self.animations))

    def render(self, bridge):
        for a in self.animations:
            a.render(bridge, 40)
