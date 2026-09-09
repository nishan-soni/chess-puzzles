#!/bin/bash
username="n15hn"
year=$(TZ=UTC date -d "today" +%Y)
month=$(TZ=UTC date -d "today" +%m)
yesterday=$(TZ=UTC date -d "today" +%Y.%m.%d)

games_raw="${GAMES_RAW:-games_raw}"
games_txt="${GAMES_TXT:-games.txt}"

mkdir -p "$games_raw"

curl -s -A "ChessTerminalApp/1.0" "https://api.chess.com/pub/player/${username}/games/${year}/${month}/pgn" > "$games_txt"

# Step 1: split into one file per game (unfiltered)
awk -v dir="$games_raw" '/^\[Event/{n++} {print > (dir "/all_game_" n ".pgn")}' "$games_txt"

# Step 2: keep only games whose EndDate matches yesterday, discard the rest
for f in "$games_raw"/all_game_*.pgn; do
    [ -e "$f" ] || continue
    if grep -q "\[EndDate \"${yesterday}\"\]" "$f"; then
        mv "$f" "${f/all_game_/game_}"
    else
        rm -f "$f"
    fi
done
