#!/bin/sh

./playgame.py --verbose --fill --log_input --log_output --log_error \
--nolaunch --log_dir game_logs --turns 200 --turntime 1000 \
--map_file maps/tron_01.map \
"python2 MyBot.py"
