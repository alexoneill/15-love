#!/usr/bin/python2
# colors.py
# nroberts 04/24/2017
from __future__ import division

class Colors:
    RED = (1.0, 0.0, 0.0)
    SKY_BLUE = (0, 0.75, 1.0)
    YELLOW = (1.0, 1.0, 0.0)
    GREEN = (0.0, 1.0, 0.0)
    PURPLE = (0.83, 0.34, 0.78)
    WHITE = (1.0, 1.0, 1.0)
    BLANK = (0.0, 0.0, 0.0)

    @staticmethod
    def fade(color, rate):
        return tuple(map(lambda x: x * rate, color))

    @staticmethod
    def weighted_avg(color1, color2, wt1, wt2):
        if wt1 == 0 and wt2 == 0:
            return Colors.WHITE # avoid divide by 0
        zipped = zip(color1, color2)
        weighted = map(lambda (x, y): (wt1 * x + wt2 * y) / (wt1 + wt2), zipped)
        return tuple(weighted)
