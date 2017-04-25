#!/usr/bin/python2
# tennis_show.py
# nroberts 04/10/2017

from show import Show
from bridge import Bridge
from colors import Colors
from animations import *
import random

# print diagnostic information for unrecognized event
def unrecognized_event(name):
    def print_error(data):
        print "Unrecognized event. Name: %s, Data: %s" % (name, data)
    return print_error

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

        p1_color = Colors.CORAL
        p2_color = Colors.SKY_BLUE
        ball_color = Colors.LIME

        # how long to make the swing
        max_swing = 35 # sequences

        p1 = Player(color=p1_color, origin=p1_seq, max_swing=max_swing, velocity=1)
        p2 = Player(color=p2_color, origin=p2_seq, max_swing=max_swing, velocity=-1)
        ball = Ball(color=ball_color, origin=p1_seq, max_seq=p2_seq, velocity=3)

        # player 1 serves first
        p1.serving = True

        # define what objects game should update every loop
        self.moving_objects = [ p1, p2, ball ]

        # set up instance variables
        self.p1, self.p2, self.ball = p1, p2, ball

        # define what functions we enter at the start
        self.actions = { "start_show" : self.start_show }

        #  player 1 and player 2
        self.players = { 1 : p1, 2 : p2 }

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

        # do all the current animations. (use ``keys'' so we can delete keys as we go)
        for key in self.actions.keys():
            self.actions[key](event)

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
        del self.actions["start_show"]
        self.actions["game_loop"] = self.game_loop

    """****************************************************************
    *  In the game loop, we render the balls and player swings, check *
    *  for hits, and tell the balls and the players to update.        *
    ****************************************************************"""
    def game_loop(self, event):
        if event:
            name, data = event
            # Python's version of a switch statement? It's event dispatch
            { "swing" : self.swing,
              "press" : self.press  }.get(name, unrecognized_event(name))(data)

        fade_frames = 20 #frames
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
            print "Player 1 swung"
            self.outqueue.put(("swing", { "player": 1 }))
            player_swing(self.p1, opponent=self.p2)
        elif data["player"] == 2:
            print "Player 2 swung"
            self.outqueue.put(("swing", { "player": 2 }))
            player_swing(self.p2, opponent=self.p1)

    # button press event received
    def press(self, data):
        player = self.players[data["player"]]
        if data["shape"] == "square":
            player.color = Colors.PURPLE
        elif data["shape"] == "circle":
            player.color = Colors.CORAL
        elif data["shape"] == "triangle":
            player.color = Colors.LIME
        elif data["shape"] == "x":
            player.color = Colors.SKY_BLUE

    def check_for_hit(self, player):
        ball = self.ball
        if player.is_active and ball.is_active:
            pseq = player.get_seq()
            bseq = ball.get_seq()

            # only hit when ball color is same color as player color
            if player.color != ball.color:
                return

            # hit ball if it has crossed where the player is swinging
            if player.velocity > 0 and ball.velocity < 0 and bseq <= pseq:
                print "Player 1 hit the ball"
                ball.hit()
            elif player.velocity < 0 and ball.velocity > 0 and bseq >= pseq:
                print "Player 2 hit the ball"
                ball.hit()

    # show several animations at once
    def animate(self, animations, on_complete):
        any_active = False

        # update and render all animations
        for animation in animations:
            if animation.is_active:
                any_active = True
                animation.render(self.bridge)
                animation.update()

        # if there's nothing left to animate, resume normal flow
        if not any_active:
            del self.actions["animate"]
            on_complete()


    # Award points to a player
    def on_missed_ball(self, awarded_player):
        player = self.players[awarded_player]
        player.score += 1

        print "Player %d now has score %d" % (awarded_player, player.score)

        # stop players from swinging
        self.p1.is_active = False
        self.p2.is_active = False

        # stop running game loop
        del self.actions["game_loop"]

        # TODO: Display score in some way on the bridge

        # what to do after showing red animation
        def on_complete():
            if player.score == 4:
                self.actions["firework_show"] = self.firework_show
            else:
                print "Resuming game loop"
                self.actions["game_loop"] = self.game_loop

        # Engulf entire bridge in red after a missed point
        animations = [ ScoreAnimation(p1=self.p1, p2=self.p2, color=player.color) ]
        self.actions["animate"] = lambda event: self.animate(animations, on_complete)

    # Show a show at the end for the winning player (eventually)
    def firework_show(self, _):
        print "Showing fireworks"
        winning_player = 1 if self.players[1].score == 4 else 2 # decide which player won
        self.outqueue.put (("gameover", { "winner": winning_player }))
        # TODO: Make a fun firework show at the end. Maybe design in Lumiverse??
        self.running = False # just end the show for now
