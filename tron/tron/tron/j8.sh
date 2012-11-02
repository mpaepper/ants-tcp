#!/bin/sh

./playgame.py --verbose --fill --log_input --log_output --log_error \
--nolaunch --log_dir game_logs --turns 500 --turntime 1000 \
--map_file maps/test/test_p02_01.map \
/home/smiley/ast/source/ocaml_asteroids/MyBot.native \
/home/smiley/ast/source/ocaml_asteroids/MyBot.native \
