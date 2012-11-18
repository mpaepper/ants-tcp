#!/usr/bin/env python
import sys
import traceback
import random
import time
from collections import defaultdict
from math import sqrt

WATER = -1
LAND = -2

MAP_OBJECT = '.%'

HEADING = {'n': (-1, 0),
           'e': (0, 1),
           's': (1, 0),
           'w': (0, -1)}
RIGHT = {'n': 'e',
         'e': 's',
         's': 'w',
         'w': 'n'}
LEFT = {'n': 'w',
        'e': 'n',
        's': 'e',
        'w': 's'}
BEHIND = {'n': 's',
          's': 'n',
          'e': 'w',
          'w': 'e'}

# Some instances of the word "ant" in comments have been replaced by "agent",
# and sometimes what it says is no longer actually what it does. If you see
# an erroneous comment, feel free to fix it.
class Tron():
    def __init__(self):
        self.cols = None
        self.rows = None
        self.map = None
        self.agent_list = defaultdict(list)
        self.dead_list = defaultdict(list)
        self.turntime = 0
        self.loadtime = 0
        self.player_id = None
        self.my_agent = None
        self.turn_start_time = None
        self.turns = 0
        self.water = []

    def setup_map(self):
        self.map = [[LAND for col in range(self.cols)]
                    for row in range(self.rows)]
        for row, col in self.water:
            self.map[row][col] = WATER

    def setup(self, data):
        'parse initial input and setup starting game state'
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                key = tokens[0]
                if key == 'cols':
                    self.cols = int(tokens[1])
                    if not self.rows == None:
                        self.setup_map()
                elif key == 'rows':
                    self.rows = int(tokens[1])
                    if not self.cols == None:
                        self.setup_map()
                elif key == 'player_seed':
                    random.seed(int(tokens[1]))
                elif key == 'turntime':
                    self.turntime = int(tokens[1])
                elif key == 'loadtime':
                    self.loadtime = int(tokens[1])
                elif key == 'player_id':
                    self.player_id = int(tokens[1])
                    self.my_agent = self.player_id
                elif key == 'viewradius2':
                    self.viewradius2 = int(tokens[1])
                elif key == 'attackradius2':
                    self.attackradius2 = int(tokens[1])
                elif key == 'spawnradius2':
                    self.spawnradius2 = int(tokens[1])
                elif key == 'turns':
                    self.turns = int(tokens[1])
                elif tokens[0] == 'w':
                    self.water.append((int(tokens[1]), int(tokens[2])))
        self.setup_map()

    def update(self, data):
        'parse engine input and update the game state'
        # clear old values
        self.agent_list = defaultdict(list)
        self.dead_list = defaultdict(list)
        # start timer
        self.turn_start_time = time.time()
        
        # update agent list
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                if len(tokens) >= 3:
                    row = int(tokens[1])
                    col = int(tokens[2])
                    if tokens[0] == 'w':
                        self.map[row][col] = WATER
                    else:
                        if tokens[0] == 'a':
                            owner = int(tokens[4])
                            try:
                                self.map[row][col] = owner
                                self.agent_list[(row, col)] = owner
                            except IndexError:
                                sys.stderr.write(('IndexError at {0}, {1}'.format(row, col)))
                        elif tokens[0] == 'd':
                            # add to the dead list
                            owner = int(tokens[4])
                            self.dead_list[(row, col)].append(owner)
                        
    def time_remaining(self):
        return self.turntime - int(1000 * (time.time() - self.turn_start_time))
    
    def issue_order(self, order):
        'issue an order by writing the proper ant location and direction'
        (row, col), direction = order
        sys.stdout.write('o %s %s %s\n' % (row, col, direction))
        sys.stdout.flush()
        
    def finish_turn(self):
        'finish the turn by writing the go line'
        sys.stdout.write('go\n')
        sys.stdout.flush()
    
    def my_agents(self):
        'return a list of all my agents'
        return [(row, col) for (row, col), owner in self.agent_list.items()
                    if owner == self.my_agent]

    def enemy_agents(self):
        'return a list of all visible enemy agents'
        return [((row, col), owner)
                    for (row, col), owner in self.agent_list.items()
                    if owner != self.my_agent]

    def food(self):
        'return a list of all food locations'
        return self.food_list[:]

    def passable(self, loc):
        'true if land'
        row, col = loc
        return self.map[row][col] == LAND
    
    def unoccupied(self, loc):
        'same as passable in Tron, this is a legacy from Ants'
        row, col = loc
        return self.map[row][col] == LAND

    def destination(self, loc, direction):
        'calculate a new location given the direction and wrap correctly'
        row, col = loc
        d_row, d_col = HEADING[direction]
        return ((row + d_row) % self.rows, (col + d_col) % self.cols)        

    def distance(self, loc1, loc2):
        'calculate the closest distance between to locations (from Ants)'
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.cols - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.rows - abs(row1 - row2))
        return d_row + d_col

    def direction(self, loc1, loc2):
        'determine the 1 or 2 fastest (closest) directions to reach a location'
        row1, col1 = loc1
        row2, col2 = loc2
        height2 = self.rows//2
        width2 = self.cols//2
        d = []
        if row1 < row2:
            if row2 - row1 >= height2:
                d.append('n')
            if row2 - row1 <= height2:
                d.append('s')
        if row2 < row1:
            if row1 - row2 >= height2:
                d.append('s')
            if row1 - row2 <= height2:
                d.append('n')
        if col1 < col2:
            if col2 - col1 >= width2:
                d.append('w')
            if col2 - col1 <= width2:
                d.append('e')
        if col2 < col1:
            if col1 - col2 >= width2:
                d.append('e')
            if col1 - col2 <= width2:
                d.append('w')
        return d

    def render_text_map(self):
        'return a pretty string representing the map'
        tmp = ''
        for row in self.map:
            tmp += '# %s\n' % ''.join([MAP_RENDER[col] for col in row])
        return tmp

    # static methods are not tied to a class and don't have self passed in
    # this is a python decorator
    @staticmethod
    def run(bot):
        'parse input, update game state and call the bot classes do_turn method'
        tron = Tron()
        map_data = ''
        while(True):
            try:
                current_line = sys.stdin.readline().rstrip('\r\n') # string new line char
                if current_line.lower() == 'ready':
                    tron.setup(map_data)
                    bot.do_setup(tron)
                    tron.finish_turn()
                    map_data = ''
                elif current_line.lower() == 'go':
                    tron.update(map_data)
#                    print >> sys.stderr, tron.agent_list
                    # call the do_turn method of the class passed in
                    bot.do_turn(tron)
                    tron.finish_turn()
                    map_data = ''
                else:
                    map_data += current_line + '\n'
            except EOFError:
                break
            except KeyboardInterrupt:
                raise
            except:
                # don't raise error or return so that bot attempts to stay alive
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
