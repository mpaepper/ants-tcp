#!/usr/bin/env python
from asteroids import *

class HoldBot:
    def do_turn(self, asteroids):
        pass

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        Asteroids.run(HoldBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
