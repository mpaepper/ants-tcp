#!/bin/sh

./playgame.py --verbose --fill --log_input --log_output --log_error \
--nolaunch --log_dir game_logs --turns 500 --turntime 1000 \
--map_file maps/test/test_p04_02.map \
"python dist/sample_bots/python/LeftyBot.py" \
"python dist/sample_bots/python/RandomBot.py" \
/home/smiley/ast/source/ocaml_asteroids/MyBot.native \
/home/smiley/ast/source/ocaml_asteroids/MyBot.native \
