#!/bin/sh

./playgame.py --verbose --fill --log_input --log_output --log_error --nolaunch --log_dir game_logs --turns 500 --map_file maps/test/planetwars_01.map "python dist/sample_bots/python/LeftyBot.py" "python dist/sample_bots/python/RandomBot.py"
