# async_move.py
# aoneill - 04/16/17

import threading
import time

from libs import psmove

class AsyncPSMove(threading.Thread):
  '''
  Asynchronous class designed to update the associated PSMove controller
  at a pre-defined frame rate.

  This avoids having the controller lose its light / rumble after not having
  received an update recently
  '''

  # Updates per second
  FPS = 40.0

  def __init__(self, num):
    # Initialize all internal state
    super(AsyncPSMove, self).__init__()

    self.num = num
    self.move = psmove.PSMove(num)

    self._running = True
    self._leds = (0, 0, 0)
    self._rumble = 0

    self._trigger = 0
    self._temp = 0
    self._batt = 0

  # Output on the controller
  def leds(self, r, g, b):
    self._leds = (r, g, b)

  def rumble(self, rumble):
    self._rumble = rumble

  def off(self):
    self._leds = (0, 0, 0)
    self._rumble = 0

  # Data from the controller
  def trigger(self):
    return self._trigger

  def temperature(self):
    return self._temp

  def battery(self):
    return self._batt

  def accel(self):
    return self._accel

  def gyro(self):
    return self._gyro

  def magno(self):
    return self._magno

  # Threading methods
  def run(self):
    while(self._running):
      # Get inputs
      if(self.move.poll()):
        self._trigger = self.move.get_trigger()
        self._temp = self.move.get_temperature()
        self._batt = self.move.get_battery()

        self._accel = (self.move.ax, self.move.ay, self.move.az)
        self._gyro = (self.move.gx, self.move.gy, self.move.gz)
        self._magno = (self.move.mx, self.move.my, self.move.mz)

      # Set outputs
      self.move.set_leds(*self._leds)
      self.move.set_rumble(self._rumble)
      self.move.update_leds()

      # 40 FPS
      time.sleep(1.0 / AsyncPSMove.FPS)

  def stop(self):
    self._running = False
