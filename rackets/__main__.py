# __main__.py
# aoneill - 04/24/17

import sys

from src import text_racket

# Main method when running the racket driver code
def main():
  # Get a text-based racket and constantly update it
  tracket = text_racket.TextRacket()
  while(True):
    tracket.update()

if(__name__ == '__main__'):
  main(*sys.argv[1:])
