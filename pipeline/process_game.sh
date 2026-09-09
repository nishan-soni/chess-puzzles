#!/bin/bash
game_file="$1"
base=$(basename "$game_file" .pgn)
outdir="${OUTDIR:-results}/${base}"
debug_dir="${outdir}/debug"
mkdir -p "$debug_dir"

pgn-extract -Wepd "$game_file" 2>/dev/null | awk 'NF {print $1, $2, $3, $4}' > "${debug_dir}/positions.txt"

awk '{ printf "position fen %s\ngo depth 5\n", $0 }' "${debug_dir}/positions.txt" > "${debug_dir}/all_commands.txt"
echo "quit" >> "${debug_dir}/all_commands.txt"

stockfish < "${debug_dir}/all_commands.txt" | grep -E "^info depth 5 .*multipv 1" | awk 'NF' > "${debug_dir}/all_evaluations.txt"

paste "${debug_dir}/positions.txt" "${debug_dir}/all_evaluations.txt" | awk 'NF' > "${debug_dir}/fen_eval.txt"
grep -oE 'score cp -?[0-9]+' "${debug_dir}/fen_eval.txt" | grep -oE '\-?[0-9]+' | awk 'NF' > "${debug_dir}/scores_raw.txt"
awk 'NR > 1 { d = $1 + prev; if (d < 0) d = -d; if (d > 320) print d, NR-1, NR } { prev = $1 }' "${debug_dir}/scores_raw.txt" | sort -rn | awk 'NF' > "${debug_dir}/swings.txt"


awk 'NF {print $3}' "${debug_dir}/swings.txt" | while read -r next_line; do
    [ -z "$next_line" ] && continue
    next_fen=$(sed -n "${next_line}p" "${debug_dir}/fen_eval.txt")
    [ -n "$next_fen" ] && printf "%s\n" "$next_fen"
done | tee "${debug_dir}/puzzles.txt" >> "${PUZZLES_FILE:-puzzles.txt}"