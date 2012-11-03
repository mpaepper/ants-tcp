#!/bin/sh

./playgame.py --verbose --fill --log_input --log_output --log_error \
--log_dir game_logs --turns 1000 --turntime 1000 \
--map_file maps/tron_05.map \
"python2 dist/starter_bots/python/MyBot.py"
