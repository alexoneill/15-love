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

def argmax(f, choices):
    max = None
    arg = None
    for c in choices:
        val = f(c)
        if max == None or val > max:
            max = val
            arg = c
    return arg

def sign(x): return 1 if x > 0 else -1

class TennisShow(Show):

    NUM_FIREWORKS = 20 # number of fireworks to show at the end
    POINTS_TO_WIN = 4 # number of points to win
    STRENGTH_THRESHOLD = 0.2 # threshold under which to not count the swing

    def init(self):
        # offset of start panel for player 1 and player 2
        p1_seq = Bridge.SEQ_LO + 11
        p2_seq = Bridge.SEQ_HI

        ball_color = Colors.YELLOW

        # how long to make the swing
        max_swing = 28 # sequences

        p1 = Player(color=None, origin=p1_seq, max_swing=max_swing, velocity=2)
        p2 = Player(color=None, origin=p2_seq, max_swing=max_swing, velocity=-2)
        ball = Ball(color=ball_color, origin=p1_seq, max_seq=p2_seq, velocity=3)

        # p1 serves first
        p1.serving = True

        # define what objects game should update every loop
        self.moving_objects = [ p1, p2, ball ]

        # set up instance variables
        self.p1, self.p2, self.ball = p1, p2, ball

        #  player 1 and player 2
        self.players = { 1 : p1, 2 : p2 }

        #show animation on the end of the bridge
        start = Bridge.SEQ_LO
        end = self.p1.origin - 1
        color = Colors.BLANK
        self.end_bridge_animation = TransitionAnimation(start=start, end=end, color=color)
        end_bridge = self.animate([ self.end_bridge_animation ])

        # define what functions we enter at the start
        self.actions = { "start_show" : self.start_show, "end_bridge": end_bridge }

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

        # globally check for reset event
        if event:
            print "Received %s" % str(event)
            name, data = event
            if name == "game_reset":
                self.reset()
                return

        # do all the current animations. (use ``keys'' so we can delete keys as we go)
        for key in self.actions.keys():
            # have default action if key has been since deleted
            self.actions.get(key, lambda _: None)(event)

    """*******************************************************
    * Restart game completely, going back to color selection *
    *******************************************************"""
    def reset(self, **kwargs):
        print "Restarting game"
        self.outqueue.put(("game_restart", { "player_num": 1 }))
        self.outqueue.put(("game_restart", { "player_num": 2 }))
        self.init() # just call the init function again

    def reset_rally(self):
        print "Starting game loop"

        # make the end of the bridge transition to the next color
        self.end_bridge_animation.next_color = Colors.weighted_avg(
            self.p1.color, self.p2.color, self.p1.score, self.p2.score
        )

        # inform player they're serving
        serving_player = 1 if self.players[1].serving else 2
        self.outqueue.put(("game_is_server", { "player_num": serving_player }))
        self.actions["game_loop"] = self.game_loop

        # get ball ready to be served
        ball = self.ball
        ball.is_active = True
        ball.counter = 1.0 # reset speed multiplier
        ball.velocity = 0
        if serving_player == 1:
            ball.x = self.p1.origin + self.p1.max_swing - 3
            lo, hi = ball.x - 3, ball.x
            print "Ball spans [%d, %d]" % (lo, hi)
        else:
            ball.x = self.p2.origin - self.p2.max_swing + 3
            lo, hi = ball.x, ball.x + 3
            print "Ball spans [%d, %d]" % (lo, hi)

        # show flashing ball animation
        animations = [ PulseAnimation(start=lo, end=hi, color=ball.color) ]
        self.actions["flashing_ball"] = self.animate(animations)

    """*******************************************************************************
    *  The start of the show performs a brief light show. When both                  *
    *  players have chosen their colors, the game loop starts with player 1 serving. *
    *******************************************************************************"""
    def start_show(self, event):
        p1 = self.p1
        p2 = self.p2
        p1_animation = PulseAnimation(start=p1.origin, end=p1.origin + p1.max_swing)
        p2_animation = PulseAnimation(start=p2.origin - p2.max_swing, end=p2.origin)

        # define how many frames to wait between both players selecting colors and starting the game
        def flash_players(event):
            if event:
                name, data = event
                {
                  "init_color_choice": self.choose_color
                }.get(name, unrecognized_event(name))(data)

            # update animations
            p1_animation.update(p1.color)
            p2_animation.update(p2.color)

            # set bridge
            p1_animation.render(self.bridge)
            p2_animation.render(self.bridge)


            # if both players have selected their color and the color has faded out
            if p1.color != None and p2.color != None and p1_animation.fade_level == 0:
                # start the game loop
                del self.actions["flash_players"]
                self.reset_rally()

        # delegate to flash_players
        del self.actions["start_show"]
        self.actions["flash_players"] = flash_players

        # make sure we capture the current event
        flash_players(event)

    def choose_color(self, data):
        color = data["color"]
        player_num = data["player_num"]
        other_player_num = TennisShow.switch(player_num)

        # get players from dictionary
        player = self.players[player_num]
        other_player = self.players[other_player_num]

        if other_player.color == color:
            print "Player %d rejected for %s" % (player_num, color)
            # inform them their color has already been chosen
            self.outqueue.put(("init_color_reject", { "player_num": player_num }))
        else:
            print "Player %d chose %s" % (player_num, color)
            # Accept player color
            self.outqueue.put(("init_color_confirm", { "player_num": player_num }))
            # set color
            player.color = color

    """****************************************************************
    *  In the game loop, we render the balls and player swings, check *
    *  for hits, and tell the balls and the players to update.        *
    ****************************************************************"""
    def game_loop(self, event):
        if event:
            name, data = event
            # Python's version of a switch statement? It's event dispatch
            {
              "game_swing" : self.swing,
            }.get(name, unrecognized_event(name))(data)

        # check for hitting the ball
        self.check_for_hit(self.p1)
        self.check_for_hit(self.p2)

        fade_frames = 30 #frames
        for obj in self.moving_objects:
          obj.render(self.bridge, fade_frames)

        # Update game objects
        for obj in self.moving_objects:
            obj.update(self)

    # swing event received
    def swing(self, data):
        def player_swing(player, opponent):
            if data["strength"] <= TennisShow.STRENGTH_THRESHOLD:
                print "Player swing too weak (%.3f <= %.3f)" % (data["strength"], TennisShow.STRENGTH_THRESHOLD)
                return
            player.set_strength(data["strength"])
            player.hand = data["hand"]
            player.swing()
            ball = self.ball
            # serve if it is your turn to serve
            if player.serving and ball.velocity == 0:
                opponent.serving = True
                player.serving = False

        if data["player_num"] == 1:
            print "Player 1 swung"
            player_swing(self.p1, opponent=self.p2)
        elif data["player_num"] == 2:
            print "Player 2 swung"
            player_swing(self.p2, opponent=self.p1)

    # check to see if ball crossed player
    def check_for_hit(self, player):
        ball = self.ball
        if player.is_active and ball.is_active:
            pseq = player.get_seq()
            bseq = ball.get_seq()

            # hit ball if it has crossed where the player is swinging
            if player.velocity > 0 and ball.velocity <= 0 and bseq <= pseq:
                self.actions.pop("flashing_ball", None) # remove animation from dict
                self.outqueue.put(("game_hit_ball", { "player_num": 1, "strength": self.p1.strength }))
                ball.hit(self.p1, self.p2.color)
                print "Player 1 hit ball at %.3f" % ball.velocity
            elif player.velocity < 0 and ball.velocity >= 0 and bseq >= pseq:
                self.actions.pop("flashing_ball", None) # remove animation from dict
                self.outqueue.put(("game_hit_ball", { "player_num": 2, "strength": self.p2.strength }))
                ball.hit(self.p2, self.p1.color)
                print "Player 2 hit ball at %.3f" % ball.velocity

    # show several animations at once
    def animate(self, animations, name=None, on_complete=lambda: None):
        def on_event(_): # curry
            any_active = False

            # update and render all animations
            for animation in animations:
                if animation.is_active:
                    any_active = True
                    animation.render(self.bridge)
                    animation.update()

            # if there's nothing left to animate, resume normal flow
            if not any_active:
                if name: del self.actions[name]
                on_complete()

        return on_event

    @staticmethod
    def switch(player_num):
        return 1 if player_num == 2 else 2

    # Award points to a player
    def on_missed_ball(self, awarded_player):
        player = self.players[awarded_player]
        player.score += 1

        print "Player %d now has score %d" % (awarded_player, player.score)

        # send events for winning rally
        other_player = TennisShow.switch(awarded_player)
        self.outqueue.put(("game_won_rally", { "player_num": awarded_player }))
        self.outqueue.put(("game_missed_ball", { "player_num": other_player }))

        # stop players from swinging
        self.p1.is_active = False
        self.p2.is_active = False

        # stop running game loop
        del self.actions["game_loop"]

        # what to do after showing red animation
        def on_complete():
            if player.score == TennisShow.POINTS_TO_WIN:
                self.firework_show()
            else:
                self.reset_rally()

        # Engulf entire bridge in red after a missed point
        kwargs = { "p1": self.p1,
                   "p2": self.p2,
                   "color": player.color,
                   "awarded_player": awarded_player }
        animations = [ ScoreAnimation(**kwargs) ]
        self.actions["score"] = self.animate(animations, "score", on_complete)

    FIREWORK_PROBABILITY = 23 # 1 in 23
    # make new firework animations to show
    def generate_fireworks(self, animations, color, n):
        def gen(event): # curry -- maybe have players be able to interact?
            if n == 0:
                del self.actions["generate_fireworks"]
                return

            number_active = len(filter(lambda x: x.is_active, animations))

            # generate a new firework with some probability, or if there are soon to be none
            if random.randint(1, TennisShow.FIREWORK_PROBABILITY) == 1 or number_active <= 1:
                animations.append(FireworkAnimation(color))
                print "Spawning firework"
                # I <3 recursion
                self.actions["generate_fireworks"] = self.generate_fireworks(animations, color, n-1)
        return gen

    # Show a show at the end for the winning player (eventually)
    def firework_show(self):
        print "Showing fireworks"
        player_num = argmax(lambda i: self.players[i].score, [ 1, 2 ]) # player with highest score wins
        winning_player = self.players[player_num]

        self.outqueue.put(("game_over", { "player_num": 1, "winner": player_num }))
        self.outqueue.put(("game_over", { "player_num": 2, "winner": player_num }))

        color = winning_player.color
        animations = [ FireworkAnimation(color) ]

        # generate 20 fireworks
        del self.actions["end_bridge"]
        self.actions["generate_fireworks"] = self.generate_fireworks(animations, color, TennisShow.NUM_FIREWORKS)
        self.actions["fireworks"] = self.animate(animations, "fireworks", self.reset)
