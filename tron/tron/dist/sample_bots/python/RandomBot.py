#!/usr/bin/env python
import random
from asteroids import *


class RandomBot:
    def do_turn(self, asteroids):
        asteroids.issue_order([random.random() / 5, random.random() - 0.5,
                               random.randrange(0, 2)])


if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        Asteroids.run(RandomBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
