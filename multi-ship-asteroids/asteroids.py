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

class Asteroids(Game):
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
        self.turn_steps = 10
        self.m_thrust = 0.5
        self.m_turn = (pi / 16)
        self.ship_radius = 5
        map_data = self.parse_map(map_text)

        self.turn = 0
        self.num_players = (map_data["num_players"])

        self.asteroids = map_data["asteroids"]
        self.bullets = []
        self.ships = map_data["ships"]

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

    def parse_map(self, map_text):
        """ Parse the map_text into a more friendly data structure """
        width = None
        height = None
        num_players = 0
        asteroids = []
        ships = []

        for line in map_text.split("\n"):
            line = line.strip()

            # ignore blank lines and comments
            if not line or line[0] == "#":
                continue

            key, value = line.split(" ", 1)
            key = key.lower()

            if key == "players":
                num_players = int(value)
            if key == "width":
                width = int(value)
            elif key == "height":
                height = int(value)
            elif key == "a":
                values = value.split()
                category = int(values[0])
                x = float(values[1])
                y = float(values[2])
                heading = float(values[3])
                speed = float(values[4])
                asteroids.append({"category": category,
                                  "x": x,
                                  "y": y,
                                  "heading": heading,
                                  "speed": speed,
                                  "previous_x": x,
                                  "previous_y": y})
            elif key == 's':
                values = value.split()
                id = int(values[0])
                x = float(values[1])
                y = float(values[2])
                heading = float(values[3])
                speed = float(values[4])
                owner = int(values[5])
                current_x = speed * cos(heading)
                current_y = speed * sin(heading)
                ships.append({"ship_id": id,
                                "owner": owner,
                                "x": x,
                                "y": y,
                                "heading": heading,
                                "speed": speed,
                                # why combine these?
                                "current_speed": (current_x, current_y),
                                "current_hp": 2,
                                # previous_ is for (future) collision detection
                                "previous_x": x,
                                "previous_y": y,
                                "fire_when": 0,
                                "is_alive": True,
                                "processed_this_turn": False})

        return {
            "size":      (width, height),
            "asteroids": asteroids,
            "ships":   ships,
            "num_players": num_players
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
            ['s', s["ship_id"], s["x"], s["y"], s["heading"],
                  s["current_speed"][0], s["current_speed"][1], s["owner"]]
            for s in self.ships if s["is_alive"] ))
        changes.extend(sorted(
            ["a", a["category"], a["x"], a["y"], a["heading"], a["speed"]]
            for a in self.asteroids))
        changes.extend(sorted(
            ["b", b["owner"], b["x"], b["y"], b["heading"], b["speed"]]
            for b in self.bullets))
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
            if len(data) != 5:
                invalid.append((line, 'incorrectly formatted order'))
                continue

            target, thrust, turn, fire = data[1:]

            # validate the data types

            try:
                target = int(target)
            except ValueError:
                invalid.append((line, "target is not an int"))
                continue

            try:
                thrust = float(thrust)
            except ValueError:
                invalid.append((line, "thrust is not a float"))
                continue

            try:
                turn = float(turn)
            except ValueError:
                invalid.append((line, "turn is not a float"))
                continue

            try:
                tmp = bool(fire)  # I think this is non-sensical.
            except ValueError:
                invalid.append((line, "fire is not a boolean"))
                continue

            if thrust < 0 or thrust > 1:
                invalid.append((line,
                                "thrust is smaller than 0 or greater than 1"))

            if turn < -1 or turn > 1:
                invalid.append((line,
                                "turn is smaller than -1 or greater than 1"))

            # this order can be parsed
            orders.append((player, target, thrust, turn, fire))
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
        for line, (player, target, thrust, turn, fire) in zip(lines, orders):
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
            valid_orders.append((player, target, thrust, turn, fire))
            valid.append(line)
            #seen_locations.add(loc)

        return valid_orders, valid, ignored, invalid

    def do_orders(self, step_count):
        """ Execute player orders and handle conflicts
        """
        for orders in self.orders:
            for player, target, thrust, turn, fire in orders:
                self.do_ship(player, target, thrust, turn, fire, step_count)

    def wrap(self, v, limit):
        if v < 0:
            return self.wrap(v + limit, limit)
        elif v >= limit:
            return self.wrap(v - limit, limit)
        else: 
            return v
#    def wrap(self, x, y):
#        wx = self.sub_wrap(x, self.width)
#        wy = self.sub_wrap(y, self.height)
#        return wx, wy
    def do_ship(self, player, ship, thrust, turn, fire, step_count):
      ship = self.ships[ship]
      if ship["owner"] == player and ship["is_alive"] and not ship["processed_this_turn"]:
        # TODO 0.5 is the ship's max thrust, should become a variable
        real_thrust = self.m_thrust * float(thrust) / self.turn_steps
        # TODO pi/16 is the ship's max turn rate, should become a variable
        ship["heading"] += self.m_turn * float(turn) / self.turn_steps
        tx = real_thrust * cos(ship["heading"]) #/ self.turn_steps
        ty = real_thrust * sin(ship["heading"]) #/ self.turn_steps
        current_speed = (ship["current_speed"][0] + tx,
                         ship["current_speed"][1] + ty)
        ship["current_speed"] = current_speed
        ship["y"] += (current_speed[1] / self.turn_steps)
        ship["x"] += (current_speed[0] / self.turn_steps)
        ship["x"] = self.wrap(ship["x"], self.width)
        ship["y"] = self.wrap(ship["y"], self.height)
        if step_count == 0:
            ship["fire_when"] -= 1
            # TODO this doesn't compute with the bool(fire) in parse_orders
            if fire == "1" and ship["fire_when"] <= 0:
                ship["fire_when"] = 10
                impetus = 6
                ihead = ship["heading"]
                bullet_dx = impetus * cos(ihead)
                bullet_dy = impetus * sin(ihead)
                bullet_x_speed = ship["current_speed"][0] + bullet_dx
                bullet_y_speed = ship["current_speed"][1] + bullet_dy
                try:
                    bullet_heading = atan(bullet_y_speed / bullet_x_speed)
                except:
                    if bullet_y_speed < 0:
                        bullet_heading = (-pi) / 2
                    elif bullet_y_speed > 0:
                        bullet_heading = pi / 2
                    else:
                        bullet_heading = 0
                try:
                    bullet_speed = bullet_y_speed / sin(bullet_heading)
                except:
                    bullet_speed = bullet_y_speed
                bullet = { "owner": ship["owner"],
                           "x": ship["x"],
                           "y": ship["y"],
                           "previous_x": ship["x"],
                           "previous_y": ship["y"],
                           "turns_to_live": 12,
                           "heading": bullet_heading,
                           # add ship's speed to bullet's speed?
                           "speed": bullet_speed }
                for count in range(0, self.turn_steps):
                    self.update_body(bullet)
                self.bullets.append(bullet)
        ship["processed_this_turn"] = True

    def update_body(self, body):
        body["previous_x"] = body["x"]
        body["previous_y"] = body["y"]
        dx = body["speed"] * cos(body["heading"]) / self.turn_steps
        dy = body["speed"] * sin(body["heading"]) / self.turn_steps
        body["x"] = self.wrap(body["x"] + dx, self.width)
        body["y"] = self.wrap(body["y"] + dy, self.height)

    def do_non_player_movement(self, step_count):
        bullets_to_remove = []
        for asteroid in self.asteroids:
            self.update_body(asteroid)
#            asteroid["previous_x"] = asteroid["x"]
#            asteroid["previous_y"] = asteroid["y"]
#            dx = asteroid["speed"] * cos(asteroid["heading"])
#            dy = asteroid["speed"] * sin(asteroid["heading"])
#            asteroid["x"] = self.wrap(asteroid["x"] + dx, self.width)
#            asteroid["y"] = self.wrap(asteroid["y"] + dy, self.height)
        for bullet in self.bullets:
            if bullet["turns_to_live"] <= 0:
                bullets_to_remove.append(bullet)
            else:
                self.update_body(bullet)
                if step_count == 0:
                    bullet["turns_to_live"] -= 1
#                bullet["previous_x"] = bullet["x"]
#                bullet["previous_y"] = bullet["y"]
#                dx = bullet["speed"] * cos(bullet["heading"])
#                dy = bullet["speed"] * sin(bullet["heading"])
#                bullet["x"] = self.wrap (bullet["x"] + dx, self.width)
#                bullet["y"] = self.wrap (bullet["y"] + dy, self.height)
        # players can still move due to inertia even if they didn't give orders
        for ship in self.ships:
            if not ship["processed_this_turn"]:
                self.do_ship(ship["owner"], ship["ship_id"], 0, 0 ,0, step_count)
        self.remove_bullets(bullets_to_remove)

    def remove_bullets(self, bullets):
        for bullet in bullets:
            try:
                self.bullets.remove(bullet)
            except ValueError:
                pass

    def kill_ship(self, ship):
        ship["is_alive"] = False
        ship["current_hp"] = 0

    def wrap_distance(self, p1, p2, size):
        d = abs(p1 - p2)
        if d > (size / 2):
            return (d - size)
        else: return d

    def distance(self, x1, y1, x2, y2):
        x_dist = self.wrap_distance (x1, x2, self.width)
        y_dist = self.wrap_distance (y1, y2, self.height)
        return sqrt((x_dist * x_dist) + (y_dist * y_dist))

    def do_collisions(self):
        asteroids_to_break = []
        ships_to_kill = []
        bullets_to_remove = []
        for ship in self.ships:  # has become self.ships
          if ship["is_alive"]:
            sx = ship["x"]
            sy = ship["y"]
            for asteroid in self.asteroids:
                ax = asteroid["x"]
                ay = asteroid["y"]
#                dx = sx - ax
#                dy = sy - ay
                # TODO this doesn't work near the edges when the objects are
                #      visually on opposite sides
                # TODO distance nees its own function
#                distance = sqrt((dx * dx) + (dy * dy))
                distance = self.distance(sx, sy, ax, ay)
                category = asteroid["category"]
                asteroid_radius = (category + 1) * (category + 1)

                ### hmmm, i think this is wrong..
                #~ radius_to_check = 5  # ship's hit bubble = 5
                #~ if asteroid_radius > radius_to_check:
                    #~ radius_to_check = asteroid_radius
                #~ if distance <= radius_to_check:
                
                ### instead, collide, when the bubbles touch!
                ship_radius = self.ship_radius  # ship's hit bubble = 5
                if distance <= asteroid_radius + ship_radius:
                    self.score[ship["owner"]] -= 1
                    ships_to_kill.append(ship)
                    break
            for bullet in self.bullets:
                bx = bullet["x"]
                by = bullet["y"]
#                dx = sx - bx
#                dy = sy - by
                # TODO this doesn't work near the edges when the objects are
                #      visually on opposite sides
                # TODO distance nees its own function
#                distance = sqrt((dx * dx) + (dy * dy))
                distance = self.distance(bx, by, sx, sy)
                # TODO 5 is the ship's size, should become a variable
                if distance <= 5:
                    self.score[bullet["owner"]] += 1
                    bullets_to_remove.append(bullet)
                    ships_to_kill.append(ship)
                    break
        for asteroid in self.asteroids:
            ax = asteroid["x"]
            ay = asteroid["y"]
            for bullet in self.bullets:
                bx = bullet["x"]
                by = bullet["y"]
#                dx = ax - bx
#                dy = ay - by
                # TODO this doesn't work near the edges when the objects are
                #      visually on opposite sides
                # TODO distance nees its own function
#                distance = sqrt((dx * dx) + (dy * dy))
                distance = self.distance(ax, ay, bx, by)
                category = asteroid["category"]
                # TODO should get its own function
                asteroid_radius = (category + 1) * (category + 1)
                if distance <= asteroid_radius:
                    asteroids_to_break.append(asteroid)
                    bullets_to_remove.append(bullet)
                    break
        self.remove_bullets(bullets_to_remove)
        for ship in ships_to_kill:
            self.kill_ship(ship)
        for asteroid in asteroids_to_break:
            category = asteroid["category"] - 1
            # currently between 2 and 4 asteroids of category - 1 are spawned
            for i in range(0, randrange(2,5)):
                if category <= 0:
                    break
                x = asteroid["x"]
                y = asteroid["y"]
                heading = random() * 2 * pi
                speed = random() * 2
                self.asteroids.append({"category": category,
                                       "x": x,
                                       "y": y,
                                       "heading": heading,
                                       "speed": speed,
                                       "previous_x": x,
                                       "previous_y": y})
            self.asteroids.remove(asteroid)

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
        players = self.remaining_players()
        if len(players) == 1:
            for player in range(self.num_players):
                self.score[player] += self.bonus[player]

        self.calc_significant_turns()

        # check if a rule change lengthens games needlessly
        if self.cutoff is None:
            self.cutoff = 'turn limit reached'

    def start_turn(self):
        """ Called by engine at the start of the turn """
        self.turn += 1
        self.orders = [[] for _ in range(self.num_players)]

    def update_game_state(self):
        for count in range(0, self.turn_steps):
            for ship in self.ships:
                ship["processed_this_turn"] = False
            self.do_orders(count)
            self.do_non_player_movement(count)
            self.do_collisions()

    def finish_turn(self):
        """ Called by engine at the end of the turn """
        self.update_game_state()
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
        result.append(['turn_steps', self.turn_steps])
        result.append(['m_thrust', self.m_thrust])
        result.append(['m_turn', self.m_turn])
        result.append(['ship_radius', self.ship_radius])
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
        if self.killed[player]: return False
        result = False
        for ship in self.ships:
            if ship["owner"] == player and ship["current_hp"] > 0:
                result = True
                break
        self.killed[player] = (self.killed[player] or (not result))
        return result

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
        stats["asteroids"] = len(self.asteroids)
        stats["bullets"] = len(self.bullets)
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
