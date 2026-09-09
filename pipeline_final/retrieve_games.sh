#!/bin/bash
username="n15hn"
year=$(TZ=UTC date -d "yesterday" +%Y)
month=$(TZ=UTC date -d "yesterday" +%m)
yesterday=$(TZ=UTC date -d "yesterday" +%Y.%m.%d)

curl -s -A "ChessTerminalApp/1.0" "https://api.chess.com/pub/player/${username}/games/${year}/${month}/pgn" > games.txt

# Step 1: split into one file per game (unfiltered)
awk '/^\[Event/{n++} {print > ("games_raw/all_game_" n ".pgn")}' games.txt

# Step 2: keep only games whose EndDate matches yesterday, discard the rest
for f in games_raw/all_game_*.pgn; do
    if grep -q "\[EndDate \"${yesterday}\"\]" "$f"; then
        mv "$f" "${f/all_game_/game_}"
    else
        rm -f "$f"
    fi
done