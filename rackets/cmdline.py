# simple.py
# aoneill - 04/16/17

import sys

import async_move

BUTTONS = [
    psmove.Btn_SQUARE,
    psmove.Btn_TRIANGLE,
    psmove.Btn_CROSS,
    psmove.Btn_CIRCLE,
]

def bound(num, lower, upper):
  return min(upper, max(lower, num))

def main():
  if(psmove.count_connected() == 0):
    print 'err: No controllers connected! See `psmove pair\''
    return

  # Pair!
  controller = async_move.AsyncPSMove(0)
  controller.start()

  # Greeting
  print 'PSMove Shell. Enter `h\' for help!'

  # Simple commandline
  while(True):
    try:
      cmd = raw_input('psmove >>> ')
      if(not cmd): continue
    except EOFError:
      print
      break

    tokens = cmd.strip().split()
    try:
      # Help menu
      if(tokens[0] == 'h'):
        print 's [0-255]: Select the controller'
        print 'r [0-255]: Sets the rumble'
        print 'l [0-255] [0-255] [0-255]: Sets the lights'
        print 'q: Exit'

      # Select controller
      elif(tokens[0] == 's'):
        id_num = bound(int(tokens[1]), 0, 255)
        controller.stop()
        controller = async_move.AsyncPSMove(0)
        controller.start()

      # Set controller rumble
      elif(tokens[0] == 'r'):
        strength = bound(int(tokens[1]), 0, 255)
        controller.rumble(strength)

      # Set controller lights
      elif(tokens[0] == 'l'):
        leds = tuple(map(lambda x: bound(int(x), 0, 255), tokens[1:]))
        controller.leds(*leds)

      # Quit
      elif(tokens[0] == 'q'):
        break

      else:
        raise Exception

    except:
      print 'err: Unrecognized command'

  # Cleanup
  controller.stop()

if(__name__ == '__main__'):
  main(*sys.argv[1:])
