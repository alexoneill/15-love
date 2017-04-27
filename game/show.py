#!/usr/bin/python2
# show.py
# authored by f16_group1

from __future__ import division, print_function
import Queue
import time

# Clock object that can sleep for 1 frame
class Clock(object):
    def __init__(self):
        self.last_tick = time.time()

    # Sleep for 1 frame, printing message to stdout if timing delayed
    def tick(self, framerate):
        sec_per_frame = 1.0 / framerate
        diff = time.time() - self.last_tick
        while diff < sec_per_frame:
            diff = time.time() - self.last_tick
        if diff > 1.05 * sec_per_frame:
            print("Warning: tick is not being called fast enough\n")
        self.last_tick = time.time()

# Abstract class for defining the display loop of a show
class Show(object):
    def __init__(self, bridge, inqueue, outqueue):
        self.bridge = bridge
        self.running = True
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.clock = Clock()
        self.init()

    # Blocking method that enters game loop
    def run(self, framerate=40):
        while self.running:
            self.update()
            self.bridge.update()
            self.clock.tick(framerate)

    def stop(self):
       self.running = False

    # (Nonblocking) puts the event name + data on the outqueue
    def send_event(self, event_name, data=None):
        self.outqueue.put((event_name, data))

    # (Nonblocking) dequeues from the inqueue, returning None if it is empty
    def receive_event(self):
        try:
            return self.inqueue.get_nowait()
        except Queue.Empty:
            return None

    def update(self):
        """ Override me """
        raise NotImplementedError

    def init(self):
        """ Override me """
        raise NotImplementedError
