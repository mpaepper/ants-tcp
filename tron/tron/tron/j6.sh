#!/bin/sh

./playgame.py --verbose --fill --log_input --log_output --log_error \
--nolaunch --log_dir game_logs --turns 500 --turntime 300 \
--map_file maps/test/test_p04_02.map \
/home/smiley/ast/source/ocaml_asteroids/MyBot.native \
"python dist/sample_bots/python/LeftyBot.py" \
"python dist/sample_bots/python/LeftyBot.py" \
"python dist/sample_bots/python/RandomBot.py" \
