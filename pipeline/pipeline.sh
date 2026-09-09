#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/data}"
OUTDIR="$DATA_DIR/results"
GAMES_RAW="$DATA_DIR/games_raw"
PUZZLES_FILE="$DATA_DIR/puzzles.txt"
GAMES_TXT="$DATA_DIR/games.txt"

mkdir -p "$DATA_DIR" "$GAMES_RAW"
rm -rf "$OUTDIR"
rm -f "$GAMES_TXT"
rm -rf "$GAMES_RAW"/*

cd "$PROJECT_ROOT"

PUZZLES_FILE="$PUZZLES_FILE" OUTDIR="$OUTDIR" \
    GAMES_RAW="$GAMES_RAW" GAMES_TXT="$GAMES_TXT" \
    ./pipeline/retrieve_games.sh

for f in "$GAMES_RAW"/*.pgn; do
    [ -e "$f" ] || continue
    PUZZLES_FILE="$PUZZLES_FILE" OUTDIR="$OUTDIR" \
        ./pipeline/process_game.sh "$f"
done

rm -f "$GAMES_TXT"
