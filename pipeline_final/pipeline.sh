#!/bin/bash

mkdir -p games_raw
rm -f games_raw/*.pgn

./retrieve_games.sh
for f in games_raw/*.pgn; do
    ./process_game.sh "$f"
done

rm -f games.txt
rm -rf games_raw