#!/bin/bash
game_file="$1"
base=$(basename "$game_file" .pgn)
outdir="results/${base}"
debug_dir="${outdir}/debug"
mkdir -p "$debug_dir"

pgn-extract -Wepd "$game_file" 2>/dev/null | awk '{print $1, $2, $3, $4}' > "${debug_dir}/positions.txt"

awk '{ printf "position fen %s\ngo depth 5\n", $0 }' "${debug_dir}/positions.txt" > "${debug_dir}/all_commands.txt"
echo "quit" >> "${debug_dir}/all_commands.txt"

stockfish < "${debug_dir}/all_commands.txt" | grep -E "^info depth 5 .*multipv 1" > "${debug_dir}/all_evaluations.txt"

paste "${debug_dir}/positions.txt" "${debug_dir}/all_evaluations.txt" > "${debug_dir}/fen_eval.txt"
grep -oE 'score cp -?[0-9]+' "${debug_dir}/fen_eval.txt" | grep -oE '\-?[0-9]+' > "${debug_dir}/scores_raw.txt"
awk 'NR > 1 { d = $1 + prev; if (d < 0) d = -d; if (d > 260) print d, NR-1, NR } { prev = $1 }' "${debug_dir}/scores_raw.txt" | sort -rn > "${debug_dir}/swings.txt"


awk '{print $2, $3}' "${debug_dir}/swings.txt" | while read -r prev_line next_line; do
    prev_fen=$(sed -n "${prev_line}p" "${debug_dir}/fen_eval.txt")
    next_fen=$(sed -n "${next_line}p" "${debug_dir}/fen_eval.txt")
    printf "%s <<blundered move>> %s\n" "$prev_fen" "$next_fen"
done > "${outdir}/puzzle_candidates.txt"