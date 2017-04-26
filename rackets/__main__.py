# __main__.py
# aoneill - 04/24/17

import os
import socket
import sys

from src import game_racket
from src import text_racket

# Main method when running the racket driver code
def main(typ = 'game'):
  if(typ == 'game'):
    if(('PB_15LOVE_IP' not in os.environ) or
        ('PB_15LOVE_IP' not in os.environ)):
      print 'Missing PB_15LOVE_IP or PB_15LOVE_PORT!'
      return 1

    # Get server parameters
    ip = os.environ['PB_15LOVE_IP']
    port = os.environ['PB_15LOVE_PORT']

    # Connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, int(port)))

    # Get a text-based racket and constantly update it
    gracket = game_racket.GameRacket(client, 2)
    while(True):
      gracket.update()

  elif(typ == 'text'):
    # Get a text-based racket and constantly update it
    tracket = text_racket.TextRacket()
    while(True):
      tracket.update()

  return 0

if(__name__ == '__main__'):
  sys.exit(main(*sys.argv[1:]))
