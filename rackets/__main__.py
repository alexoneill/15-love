# __main__.py
# aoneill - 04/24/17

import os
import socket
import sys

from src.rackets import sio_racket

# Main method when running the racket driver code
def main(player = '1'):
  if(('PB_15LOVE_IP' not in os.environ) or
      ('PB_15LOVE_IP' not in os.environ)):
    print 'Missing PB_15LOVE_IP or PB_15LOVE_PORT!'
    return 1

  # Get server parameters
  ip = os.environ['PB_15LOVE_IP']
  port = os.environ['PB_15LOVE_PORT']
  player = int(player)

  # Get a text-based racket and constantly update it
  sracket = sio_racket.SIORacket(ip, port, player)
  while(True):
    sracket.update()

  return 0

if(__name__ == '__main__'):
  sys.exit(main(*sys.argv[1:]))
