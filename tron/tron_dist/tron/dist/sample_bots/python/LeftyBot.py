#!/usr/bin/env python
from asteroids import *

class LeftyBot:
    def do_turn(self, asteroids):
        asteroids.issue_order([0.05, -0.15, 1])

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        Asteroids.run(LeftyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
