#!/usr/bin/env python
from asteroids import *

class ForwardBot:
    def do_turn(self, asteroids):
        asteroids.issue_order([0.1, 0.0, 0])

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        Asteroids.run(ForwardBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
