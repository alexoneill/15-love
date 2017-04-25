# __main__.py
# aoneill - 04/24/17

import socket
import sys

from src import game_racket
from src import text_racket

# Main method when running the racket driver code
def main(typ = 'game'):
  if(typ == 'game'):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client.connect(('pbridge.adm.cs.cmu.edu', 8081))
    client.connect(('128.2.208.126', 8081))

    # Get a text-based racket and constantly update it
    gracket = game_racket.GameRacket(client, 2)
    while(True):
      gracket.update()
  elif(typ == 'text'):
    # Get a text-based racket and constantly update it
    tracket = text_racket.TextRacket()
    while(True):
      tracket.update()

if(__name__ == '__main__'):
  main(*sys.argv[1:])
