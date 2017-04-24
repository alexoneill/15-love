# __main__.py
# aoneill - 04/24/17

import sys

from src import text_racket

def main():
  tracket = text_racket.TextRacket()
  while(True):
    tracket.update()

if(__name__ == '__main__'):
  main(*sys.argv[1:])
