#!/usr/bin/python2
# animations.py
# nroberts 04/16/2017

from bridge import Bridge
from colors import Colors
import random

PLAYER_PRIORITY = 3
BALL_PRIORITY = 4
SCORE_PRIORITY = 5

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
    def init(self, end_seq):
        self.end_x = end_seq
        self.is_active = True
        self.priority = SCORE_PRIORITY

    def update(self):
        self.x += self.velocity

        # it has reached its spot, so stop it
        if ((self.velocity < 0 and self.x <= self.end_x)
         or (self.velocity > 0 and self.x >= self.end_x)):
            self.x = self.end_x
            self.velocity = 0
            self.frames_till_end = 40
            print "Score reached destination at %d" % self.x

        # run until dead
        if self.velocity == 0:
            # die
            if self.frames_till_end == 0:
                print "Score done showing"
                self.is_active = False

            self.frames_till_end -= 1

# Class for the pulse animation after someone scores
# Also displays score for each player
class ScoreAnimation(object):

    # distance between consecutive score panels
    SEPARATION = 2 # sequences
    VELOCITY = 4 # sequences per frame for score bars
    FADE_FRAMES = 10 # how long it takes to fade

    def __init__(self, p1, p2, color):
        self.p1 = p1
        self.p2 = p2
        self.color = color

        # start animation immediately
        self.state = "pulse" # pulse is where we make the whole bridge the same color
        self.pulse_frames = 40
        self.is_active = True

    def update(self):
        if self.pulse_frames > 0:
            self.pulse_frames -= 1

    def make_scorebar_animations(self):
        animations = []
        p1, p2 = self.p1, self.p2
        p1_offset = p1.origin + p1.max_swing - 4 * ScoreAnimation.SEPARATION
        p2_offset = p2.origin - p2.max_swing - 4 * ScoreAnimation.SEPARATION

        # constants used when creating animations
        v = ScoreAnimation.VELOCITY
        hi = Bridge.SEQ_HI
        lo = Bridge.SEQ_LO

        # make animations for p1 score
        for i in xrange(0, self.p1.score):
            # origin is +/- 1 so both the p1 and p2 scores display
            s1 = ScoreBars(origin=hi-1, end_seq=p1_offset, color=self.p1.color, velocity=-v)
            s2 = ScoreBars(origin=lo+1, end_seq=p2_offset, color=self.p1.color, velocity=v)
            animations.append(s1)
            animations.append(s2)
            p1_offset += ScoreAnimation.SEPARATION
            p2_offset -= ScoreAnimation.SEPARATION

        # make animations for p2 score
        for i in xrange(0, self.p2.score):
            s1 = ScoreBars(origin=hi, end_seq=p1_offset, color=self.p2.color, velocity=-v)
            s2 = ScoreBars(origin=lo, end_seq=p2_offset, color=self.p2.color, velocity=v)
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
    # max_seq is the furthest sequence the ball is allowed to go to
    def init(self, max_seq):
        self.max_seq = max_seq
        self.starting_velocity = self.velocity
        self.priority = BALL_PRIORITY

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

    def hit(self):
        # change direction when hit
        self.velocity = -self.velocity
        #self.color = random.choice(Colors.ALL) # Set to a random color

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

    def serve(self, ball):
        # set ball to active with new velocity
        ball.velocity = ball.starting_velocity * self.velocity
        ball.x =  self.origin
        print "Player hit ball"
        print "Ball starting at %d, moving with velocity %d" % (ball.x, ball.velocity)
        ball.is_active = True

    def update(self, show):
        if self.is_active:
            # advance swing in positive or negative direction
            self.x += self.velocity

            # check if the swing is in the right range
            if abs(self.x - self.origin) >= self.max_swing:
                print "Player done swinging at %d" % self.x
                self.is_active = False
