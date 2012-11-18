#!/usr/bin/env python
from asteroids import *

class LeftyBot:
    def do_turn(self, asteroids):
        asteroids.finish_turn()

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
