#!/usr/bin/env python

from random import randrange, choice, shuffle, randint, seed, random
from math import cos, pi, sin, sqrt, atan
from collections import deque, defaultdict

from fractions import Fraction
import operator
from game import Game
from copy import deepcopy
try:
    from sys import maxint
except ImportError:
    from sys import maxsize as maxint

class Wargame(Game):
    def __init__(self, options=None):
        # setup options
        map_text = options['map']
        self.turns = int(options['turns'])
        self.loadtime = int(options['loadtime'])
        self.turntime = int(options['turntime'])
        self.engine_seed = options.get('engine_seed',
                                       randint(-maxint-1, maxint))
        self.player_seed = options.get('player_seed',
                                       randint(-maxint-1, maxint))
        seed(self.engine_seed)

        self.cutoff_percent = options.get('cutoff_percent', 0.85)
        self.cutoff_turn = options.get('cutoff_turn', 150)

        self.scenario = options.get('scenario', False)

        map_data = self.parse_map(map_text)

        self.group_count = self.count_groups(map_data)

        self.turn = 0
        self.min_income = 5	#FIXME
        self.base_unit = 1000	#FIXME tell the player, maybe add to map
        self.neutral_id = 10000
        self.attack_casualty = 70
        self.defense_casualty = 60
        self.num_players = map_data["players"]
        self.player_to_begin = randint(0, self.num_players)

#        self.asteroids = map_data["asteroids"]
#        self.bullets = []
#        self.players = map_data["players"]
        self.players = []
        for count in range(0, self.num_players):
            self.players.append(dict(zip(
                ["player_id", "armies_to_place", "move_index", "finished_turn"],
                 [count, 0, 0, False])))
        # used to cutoff games early
        self.cutoff = None
        self.cutoff_bot = None # Can be ant owner, FOOD or LAND
        self.cutoff_turns = 0
        # used to calculate the turn when the winner took the lead
        self.winning_bot = None
        self.winning_turn = 0
        # used to calculate when the player rank last changed
        self.ranking_bots = None
        self.ranking_turn = 0

        # initialize size
        self.height, self.width = map_data['size']

        # declare territories and connections
        self.territory = map_data['territories']
        self.connection = map_data['connections']
        # for scenarios, the map file is followed exactly
        if self.scenario:
            # initialize ants
            #for player, player_ants in map_data['ants'].items():
            #    for ant_loc in player_ants:
            #        self.add_initial_ant(ant_loc, player)
            self.original_map = []
            for map_row in self.map:
                self.original_map.append(map_row[:])

        # initialize scores
        self.score = [0]*self.num_players
        self.bonus = [0]*self.num_players
        self.score_history = [[s] for s in self.score]

        # cache used by neighbourhood_offsets() to determine nearby squares
        self.offsets_cache = {}

        # used to track dead players, ants may still exist, but orders are not processed
        self.killed = [False for _ in range(self.num_players)]

        # used to give a different ordering of players to each player;
        # initialized to ensure that each player thinks they are player 0
        self.switch = [[None]*self.num_players + list(range(-5,0))
                       for i in range(self.num_players)]
        for i in range(self.num_players):
            self.switch[i][i] = 0

        # the engine may kill players before the game starts and this is needed
        # to prevent errors
        self.orders = [[] for i in range(self.num_players)]
        
        ### collect turns for the replay
        self.replay_data = []

    def count_groups(self, map_data):
        group = dict()
        for t in map_data['territories']:
            try:
                group[t['group']] += 1
            except:
                group[t['group']] = 1
        return group

    def player_groups(self, player):
        pgroup = dict()
        for t in self.territory:
            if t['owner'] == player['player_id']:
                try:
                    pgroup[t['group']] += 1
                except:
                    pgroup[t['group']] = 1
        return pgroup

    def complete_groups(self, player_group):
        result = 0
        for group_id, value in player_group.items():
            if self.group_count[group_id] == value and value > 0:
                result += 1
        return result

    def parse_map(self, map_text):
        """ Parse the map_text into a more friendly data structure """
        width = None
        height = None
        territory = []
        connection = []
        num_players = None

        for line in map_text.split("\n"):
            line = line.strip()

            # ignore blank lines and comments
            if not line or line[0] == "#":
                continue

            key, value = line.split(" ", 1)
            key = key.lower()

            if key == "width":
                width = int(value)
            elif key == "height":
                height = int(value)
            elif key == "players":
                num_players = int(value)
            elif key == "t":
                values = value.split()
                t_id = int(values[0])
                group = int(values[1])
                x = int(values[2])
                y = int(values[3])
                owner = int(values[4])
                armies = int(values[5])
                territory.append({"territory_id": t_id,
                                  "group": group,
                                  "x": x,
                                  "y": y,
                                  "owner": owner,
                                  "armies": armies})
            elif key == "c":
                values = value.split()
                connect_a = int(values[0])
                connect_b = int(values[1])
                connection.append({"a": connect_a,
                                   "b": connect_b})
        return {
            "size":      (width, height),
            "territories": territory,
            "connections": connection,
            "players": num_players
        }

    def render_changes(self, player):
        """ Create a string which communicates the updates to the state
        """
        updates = self.get_state_changes()
        visible_updates = []
        # next list all transient objects
        for update in updates:
            visible_updates.append(update)
        visible_updates.append([]) # newline
        return '\n'.join(' '.join(map(str,s)) for s in visible_updates)

    def get_state_changes(self):
        """ Return a list of all transient objects on the map.

            Changes are sorted so that the same state will result in the same
            output.
        """
        changes = []
        changes.extend(sorted(
            ['p', p["player_id"], p["armies_to_place"]]
            for p in self.players if self.is_alive(p["player_id"])))
        changes.extend(sorted(
            ['c', c["a"], c["b"]]
            for c in self.connection))
        changes.extend(sorted(
            ['t', t["territory_id"], t["group"], t["x"], t["y"], t["owner"], t["armies"]]
            for t in self.territory))
#        result.extend(sorted(
#            ['c', c["a"], c["b"]]
#            for c in self.connection))
 #        changes.extend(sorted(
#            ["a", a["category"], a["x"], a["y"], a["heading"], a["speed"]]
#            for a in self.asteroids))
#        changes.extend(sorted(
#            ["b", b["owner"], b["x"], b["y"], b["heading"], b["speed"]]
#            for b in self.bullets))
        return changes

    def parse_orders(self, player, lines):
        """ Parse orders from the given player

            Orders must be of the form: o thrust turn fire
            thrust must be a float between 0 and 1
            turn must be a float between -1 and 1
            direction must be an int and either 0 or 1
        """
        orders = []
        valid = []
        ignored = []
        invalid = []

        for line in lines:
            line = line.strip().lower()
            # ignore blank lines and comments
            if not line or line[0] == '#':
                continue

            if line[0] == '#':
                ignored.append((line))
                continue

            data = line.split()

            # validate data format
            if data[0] != 'o':
                invalid.append((line, 'unknown action'))
                continue
            if data[1] != 'a' and data [1] != 't' and data[1] != 'm' and data[1] != 'd':
                invalid.append((line, 'unknown action'))
                continue
            if (data[1] == 'd' and len(data) != 4) or (data[1] != 'd' and len(data) != 5):
                invalid.append((line, 'incorrectly formatted order'))
                continue

            if data[1] == 'd':
                action = 'd'
                num = data[2]
                source = -1
                target = data[3]
            else:
                action, num, source, target = data[1:]

            # validate the data types
            try:
                num = int(num)
            except ValueError:
                invalid.append((line, "num to move is not an int"))
                continue

            try:
                source = int(source)
            except ValueError:
                invalid.append((line, "source is not an int"))
                continue

            try:
                target = int(target)
            except ValueError:
                invalid.append((line, "target is not an int"))
                continue

            if num < 1:
                invalid.append((line, "num to move is smaller than 1"))

            if action == 'd' and source != -1:
                invalid.append((line, "deploy source is not -1 but should be"))

            if action != 'd' and source < 0:
                invalid.append((line, "move source less than 0"))

            if target < 0:
                invalid.append((line, "order target less than 0"))

            # this order can be parsed
            orders.append((player, action, num, source, target))
            valid.append(line)

        return orders, valid, ignored, invalid

    def validate_orders(self, player, orders, lines, ignored, invalid):
        """ Validate orders from a given player

            Location (row, col) must be ant belonging to the player
            direction must not be blocked
            Can't multiple orders to one ant
        """
        valid = []
        valid_orders = []
        seen_locations = set()
        for line, (player, action, num, source, target) in zip(lines, orders):
            ## validate orders
            #if loc in seen_locations:
            #    invalid.append((line,'duplicate order'))
            #    continue
            #try:
            #    if self.map[loc[0]][loc[1]] != player:
            #        invalid.append((line,'not player ant'))
            #        continue
            #except IndexError:
            #    invalid.append((line,'out of bounds'))
            #    continue
            #if loc[0] < 0 or loc[1] < 0:
            #    invalid.append((line,'out of bounds'))
            #    continue
            #dest = self.destination(loc, AIM[direction])
            #if self.map[dest[0]][dest[1]] in (FOOD, WATER):
            #    ignored.append((line,'move blocked'))
            #    continue

            # this order is valid!
            valid_orders.append((player, action, num, source, target))
            valid.append(line)
            #seen_locations.add(loc)

        return valid_orders, valid, ignored, invalid

    def max_orders(self):
        result = 0
        for player_orders in self.orders:
            if len(player_orders) > result:
                result = len(player_orders)
        return result

    def update_move_sequence(self):
        self.player_to_begin = self.player_to_begin + 1
        if self.player_to_begin >= self.num_players:
            self.player_to_begin = self.player_to_begin - self.num_players

    def get_move_sequence(self):
        """ Sequence for cycling through players so they all sometimes 
            get to move first
        """
        p1 = range(self.player_to_begin, self.num_players)
        result = p1 + (range(0, self.player_to_begin))
        return result

    def attack (self, player, num, source, target):
        defender_strength = self.territory[target]["armies"]
        attacker_losses = defender_strength * self.attack_casualty / 100
        defender_losses = num * self.defense_casualty / 100
        defenders_remain = self.territory[target]["armies"] - defender_losses
        attackers_remain = num - attacker_losses
        if defenders_remain < 1 and attackers_remain > 0:
            self.territory[target]["armies"] = max (0, attackers_remain)
            self.territory[source]["armies"] -= num
            self.territory[target]["owner"] = player
        elif defenders_remain > 0:
            self.territory[target]["armies"] = defenders_remain
            self.territory[source]["armies"] = max (0, attackers_remain)
        else:
            self.territory[target]["armies"] = 0
            self.territory[source]["armies"] = 0
            self.territory[target]["owner"] = self.neutral_id
            self.territory[source]["owner"] = self.neutral_id

    def transfer (self, player, num, source, target):
        self.territory[source]["armies"] -= num
        self.territory[target]["armies"] += num

    def do_move_phase_order(self, (player, action, num, source, target)):
        valid = False
        if action == "d": pass
        elif action == "a":
            if self.territory[target]["owner"] != player and num > 0 and self.territory[source]["owner"] == player and self.territory[source]["armies"] > 1:
                valid = True
                will_send = min (num, (self.territory[source]["armies"] - 1))
                self.attack (player, num, source, target)
        elif action == "t":
            if self.territory[target]["owner"] == player and self.territory[source]["owner"] == player and num > 0 and self.territory[source]["armies"] > 1:
                valid = True
                will_send = min (num, (self.territory[source]["armies"] - 1))
                self.transfer (player, num, source, target)
        elif action == "m":
            if num > 0 and self.territory[source]["armies"] > 1:
                if self.territory[source]["owner"] == player:
                    valid = True
                    will_send = min (num, (self.territory[source]["armies"] - 1))
                    if self.territory[target]["owner"] == player:
                        self.transfer (player, will_send, source, target)
                    else:
                        self.attack (player, will_send, source, target)
        return valid

    def process_next_order(self, player_index):
        """ Process one player order in which something actually happens
        """
        player = self.players[player_index]
        if not player["finished_turn"]:
            done = False
            while not done:
                if len(self.orders[player_index]) <= player["move_index"]:
                    player["finished_turn"] = True
                    done = True
                else:
                    order = self.orders[player_index][player["move_index"]]
                    valid = self.do_move_phase_order(order)
                    player["move_index"] += 1
                    if valid:
                        done = True

    def unprocessed_orders_remain(self):
        result = False
        for player in self.players:
            if player["finished_turn"] == False:
                result = True
        return result

    def deployment_orders(self, player):
        player_orders = self.orders[player["player_id"]]
        limit = len(player_orders)
        done = False
        for order in player_orders:
            if not done:
                (player_id, action, num, source, target) = order
                if action == "d":
                    player["move_index"] += 1
                    if self.territory[target]["owner"] == player_id and num > 0 and self.players[player_id]["armies_to_place"] > 0:
                        will_deploy = min (num, self.players[player_id]["armies_to_place"] - 1)
                        valid = True
                        self.territory[target]["armies"] += will_deploy
                        self.players[player_id]["armies_to_place"] -= will_deploy
                else: done = True

    def do_orders(self):
        """ Execute player orders and handle conflicts
        """
        for player in self.players:
            self.deployment_orders(player)
        self.update_move_sequence()
        sequence = self.get_move_sequence()
        while self.unprocessed_orders_remain():
            for player_index in sequence:
                self.process_next_order(player_index)
        
    def remaining_players(self):
        """ Return the players still alive """
        return [p for p in range(self.num_players) if self.is_alive(p)]

    # Common functions for all games

    def game_over(self):
        """ Determine if the game is over

            Used by the engine to determine when to finish the game.
            A game is over when there are no players remaining, or a single
              winner remaining.
        """
        if len(self.remaining_players()) < 1:
            self.cutoff = 'extermination'
            return True
        if len(self.remaining_players()) == 1:
            self.cutoff = 'lone survivor'
            return True
        #if self.cutoff_turns >= self.cutoff_turn:
        #    if self.cutoff_bot == FOOD:
        #        self.cutoff = 'food not being gathered'
        #    else:
        #        self.cutoff = 'ants not razing hills'
        #    return True
        return False

    def kill_player(self, player):
        """ Used by engine to signal that a player is out of the game """
        self.killed[player] = True

    def start_game(self):
        """ Called by engine at the start of the game """
        self.game_started = True
        
        ### append turn 0 to replay
        self.replay_data.append( self.get_state_changes() )

    def finish_game(self):
        """ Called by engine at the end of the game """
#        players = self.remaining_players()
#        if len(players) == 1:
#            for player in range(self.num_players):
#                self.score[player] += self.bonus[player]

        self.calc_significant_turns()

        # check if a rule change lengthens games needlessly
        if self.cutoff is None:
            self.cutoff = 'turn limit reached'

    def count_territories(self, player_id):
        result = 0
        for t in self.territory:
            if t["owner"] == player_id:
                result += 1
        return result

    def update_scores(self):
        for player in self.players:
            index = player["player_id"]
            self.score[index] = self.count_territories(index)

    def add_army_income(self, player):
        terri = self.count_territories(player["player_id"])
        income = max(self.min_income, int(terri / 3))
        bonus = self.complete_groups(self.player_groups(player))
        player["armies_to_place"] += (income + bonus) * self.base_unit

    def begin_player_turn(self, player):
        player["processed_this_turn"] = False
        player["finished_turn"] = False
        player["finished_deployment"] = False
        player["move_index"] = 0
        self.add_army_income(player)

    def start_turn(self):
        """ Called by engine at the start of the turn """
        self.turn += 1
        self.orders = [[] for _ in range(self.num_players)]
        for player in self.players:
            self.begin_player_turn(player)

    def finish_turn(self):
        """ Called by engine at the end of the turn """
        self.do_orders()
#        self.do_non_player_movement()
#        self.do_collisions()
        # record score in score history
        for i, s in enumerate(self.score):
            if self.is_alive(i):
                self.score_history[i].append(s)
            elif s != self.score_history[i][-1]:
                # score has changed, increase history length to proper amount
                last_score = self.score_history[i][-1]
                score_len = len(self.score_history[i])
                self.score_history[i].extend([last_score]*(self.turn-score_len))
                self.score_history[i].append(s)
        self.calc_significant_turns()
        self.update_scores()

        ### append turn to replay
        self.replay_data.append( self.get_state_changes() )

    def calc_significant_turns(self):
        ranking_bots = [sorted(self.score, reverse=True).index(x) for x in self.score]
        if self.ranking_bots != ranking_bots:
            self.ranking_turn = self.turn
        self.ranking_bots = ranking_bots

        winning_bot = [p for p in range(len(self.score)) if self.score[p] == max(self.score)]
        if self.winning_bot != winning_bot:
            self.winning_turn = self.turn
        self.winning_bot = winning_bot

    def get_state(self):
        """ Get all state changes

            Used by engine for streaming playback
        """
        updates = self.get_state_changes()
        updates.append([]) # newline
        return '\n'.join(' '.join(map(str,s)) for s in updates)

    def get_player_start(self, player=None):
        """ Get game parameters visible to players

            Used by engine to send bots startup info on turn 0
        """
        result = []
        result.append(['turn', 0])
        result.append(['loadtime', self.loadtime])
        result.append(['turntime', self.turntime])
        result.append(['player_id', player])
        result.append(['width', self.width])
        result.append(['height', self.height])
        result.append(['turns', self.turns])
        result.append(['player_seed', self.player_seed])
        result.append(['neutral_id', self.neutral_id])
        result.extend(sorted(
            ['t', t["territory_id"], t["group"], t["x"], t["y"], t["owner"], t["armies"]]
            for t in self.territory))
        result.extend(sorted(
            ['c', c["a"], c["b"]]
            for c in self.connection))
        result.extend(sorted(
            ['p', p["player_id"], p["armies_to_place"]]
            for p in self.players if self.is_alive(p["player_id"])))
        # information hidden from players
        #if player is None:
        #    result.append(['food_start', self.food_start])
        #    for line in self.get_map_output():
        #        result.append(['m',line])
        result.append([]) # newline
        return '\n'.join(' '.join(map(str,s)) for s in result)

    def get_player_state(self, player):
        """ Get state changes visible to player

            Used by engine to send state to bots
        """
        return self.render_changes(player)

    def is_alive(self, player):
        """ Determine if player is still alive

            Used by engine to determine players still in the game
        """
        if self.killed[player] or self.count_territories(player) == 0:
            return False
        else:
            return True
#            result = False
#            for ship in self.players:
#                if ship["player_id"] == player and ship["current_hp"] > 0:
#                    result = True
#                    break
#            return result

    def get_error(self, player):
        """ Returns the reason a player was killed

            Used by engine to report the error that kicked a player
              from the game
        """
        return ''

    def do_moves(self, player, moves):
        """ Called by engine to give latest player orders """
        orders, valid, ignored, invalid = self.parse_orders(player, moves)
        orders, valid, ignored, invalid = self.validate_orders(player, orders, valid, ignored, invalid)
        self.orders[player] = orders
        return valid, ['%s # %s' % ignore for ignore in ignored], ['%s # %s' % error for error in invalid]

    def get_scores(self, player=None):
        """ Gets the scores of all players

            Used by engine for ranking
        """
        if player is None:
            return self.score
        else:
            return self.order_for_player(player, self.score)

    def order_for_player(self, player, data):
        """ Orders a list of items for a players perspective of player #

            Used by engine for ending bot states
        """
        s = self.switch[player]
        return [None if i not in s else data[s.index(i)]
                for i in range(max(len(data),self.num_players))]

    def get_stats(self):
        """  Used by engine to report stats
        """
        stats = {}
        stats["territory"] = len(self.territory)
        stats["connection"] = len(self.connection)
        stats['score'] = self.score
        stats['s_alive'] = [1 if self.is_alive(player) else 0
                            for player in range(self.num_players)]
        return stats

    def get_replay(self):
        """ Return a summary of the entire game

            Used by the engine to create a replay file which may be used
            to replay the game.
        """
        replay = {}
        # required params
        replay['revision'] = 1
        replay['players'] = self.num_players

        # optional params
        replay['loadtime'] = self.loadtime
        replay['turntime'] = self.turntime
        replay['turns'] = self.turns
        replay['engine_seed'] = self.engine_seed
        replay['player_seed'] = self.player_seed

        # scores
        replay['scores'] = self.score_history
        replay['bonus'] = self.bonus
        replay['winning_turn'] = self.winning_turn
        replay['ranking_turn'] = self.ranking_turn
        replay['cutoff'] =  self.cutoff
        
        ### 
        replay['width'] = self.width
        replay['height'] = self.height
        replay['data'] = self.replay_data
        return replay
