# async_move.py
# aoneill - 04/16/17

import threading
import time

from libs import psmove

class GenericController(psmoveapi.PSMoveAPI):
  def on_update(self, controller):
    self._color = (
        controller.color.r
        controller.color.g
        controller.color.b
      )

    self._rumble = controller.rumble
    self._trigger = controller.trigger

    self._accelerometer = (
        controller.accelerometer.x
        controller.accelerometer.y
        controller.accelerometer.z
      )

    self._gyroscope = (
        controller.gyroscope.x
        controller.gyroscope.y
        controller.gyroscope.z
      )

    self._magnetometer = (
        controller.magnetometer.x
        controller.magnetometer.y
        controller.magnetometer.z
      )

    self._battery = controller.battery

    self._buttons = controller.
    self._pressed = controller.
    self._released = controller.


        print('Update controller:', controller, int(time.time() - controller.connection_time))
        print(controller.accelerometer, '->', controller.color, 'usb:', controller.usb, 'bt:', controller.bluetooth)
        up_pointing = min(1, max(0, 0.5 + 0.5 * controller.accelerometer.y))
        controller.color = psmoveapi.RGB(controller.trigger, up_pointing, 1.0 if controller.usb else 0.0)
        if controller.now_pressed(psmoveapi.Button.PS):
            self.quit = True

    def on_disconnect(self, controller):
        print('Controller disconnected:', controller)


api = RedTrigger()
while not api.quit:
    api.update()

class AsyncPSMove(threading.Thread):
  def __init__(self, num, on_event):
    super(AsyncPSMove, self).__init__()

    self.num = num
    self.move = psmove.PSMove(num)
    self.on_event = on_event

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
      time.sleep(0.025)

  def stop(self):
    self._running = False
