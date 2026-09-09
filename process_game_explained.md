# `process_game.sh` line-by-line

This file takes one PGN game and extracts candidate puzzle positions from it. The script assumes `OUTDIR` (where per-game debug files live) and `PUZZLES_FILE` (where final candidates are appended) are set by the caller; if not, they default to `results/` and `puzzles.txt`.

## Setup (lines 1–7)

- `game_file="$1"` – the PGN file passed in.
- `base=$(basename "$game_file" .pgn)` – the game filename without `.pgn`.
- `outdir="${OUTDIR:-results}/${base}"` – directory for this game's output. Defaults to `results/<game>/`.
- `debug_dir="${outdir}/debug"` – sub-folder for intermediate files.
- `mkdir -p "$debug_dir"` – create the output folders.

## Line 8 — extract positions from the game

```bash
pgn-extract -Wepd "$game_file" 2>/dev/null | awk 'NF {print $1, $2, $3, $4}' > "${debug_dir}/positions.txt"
```

- `pgn-extract -Wepd` converts the PGN into EPD/FEN-like strings, one per position.
- `2>/dev/null` throws away any stderr noise.
- `awk 'NF {print $1, $2, $3, $4}'` only prints non-empty lines and keeps the first four EPD fields (piece placement, side to move, castling, en passant). `NF` means "number of fields is non-zero".
- Output: `debug/positions.txt` with one position per line.

## Line 10 — build Stockfish input

```bash
awk '{ printf "position fen %s\ngo depth 5\n", $0 }' "${debug_dir}/positions.txt" > "${debug_dir}/all_commands.txt"
```

- For every position line, `awk` prints two Stockfish commands:
  - `position fen <fen>`
  - `go depth 5`
- The result is a single batch command file for Stockfish.

## Line 11 — quit Stockfish

```bash
echo "quit" >> "${debug_dir}/all_commands.txt"
```

- Appends `quit` so Stockfish shuts down cleanly after the batch.

## Line 13 — evaluate every position with Stockfish

```bash
stockfish < "${debug_dir}/all_commands.txt" | grep -E "^info depth 5 .*multipv 1" | awk 'NF' > "${debug_dir}/all_evaluations.txt"
```

- Sends the batch commands to Stockfish.
- `grep -E "^info depth 5 .*multipv 1"` grabs only the final `info` line from each 5-depth search (the "best line" result).
- `awk 'NF'` removes any accidental empty lines.
- Output: one `info` line per position, in the same order as `positions.txt`.

## Line 15 — pair positions with their evaluations

```bash
paste "${debug_dir}/positions.txt" "${debug_dir}/all_evaluations.txt" | awk 'NF' > "${debug_dir}/fen_eval.txt"
```

- `paste` joins the two files side-by-side with a tab, so each line is now the FEN followed by its Stockfish `info` output.
- `awk 'NF'` again strips blank lines.

## Line 16 — extract numeric centipawn scores

```bash
grep -oE 'score cp -?[0-9]+' "${debug_dir}/fen_eval.txt" | grep -oE '\-?[0-9]+' | awk 'NF' > "${debug_dir}/scores_raw.txt"
```

- First `grep -oE 'score cp -?[0-9]+'` pulls out every `score cp <number>` string.
- Second `grep -oE '\-?[0-9]+'` extracts just the signed number.
- `awk 'NF'` strips empties.
- Output: one numeric score per line in the order positions were evaluated.

## Line 17 — find big evaluation swings

```bash
awk 'NR > 1 { d = $1 + prev; if (d < 0) d = -d; if (d > 320) print d, NR-1, NR } { prev = $1 }' "${debug_dir}/scores_raw.txt" | sort -rn | awk 'NF' > "${debug_dir}/swings.txt"
```

- `NR > 1` means "skip the first line" because we need two scores to compare.
- `d = $1 + prev` compares the current score with the previous score. Since scores are from opposite sides' perspectives (they alternate), a big jump means the last move was a blunder.
- `if (d < 0) d = -d` takes the absolute value.
- `if (d > 320) print d, NR-1, NR` prints the swing size plus the two line numbers (previous position, current position) when the swing is greater than 320 centipawns.
- `prev = $1` remembers the current score for the next comparison.
- `sort -rn` sorts swings biggest-first.
- `awk 'NF'` drops blank lines.
- Output: `swings.txt` with lines like `<swing> <prev_line> <next_line>`.

## Lines 20–24 — output the candidate positions

```bash
awk 'NF {print $3}' "${debug_dir}/swings.txt" | while read -r next_line; do
    [ -z "$next_line" ] && continue
    next_fen=$(sed -n "${next_line}p" "${debug_dir}/fen_eval.txt")
    [ -n "$next_fen" ] && printf "%s\n" "$next_fen"
done | tee "${debug_dir}/puzzles.txt" >> "${PUZZLES_FILE:-puzzles.txt}"
```

- `awk 'NF {print $3}'` pulls out the third column of `swings.txt`: the line number of the **after-blunder** position.
- `while read -r next_line; do ... done` loops over each of those line numbers.
- `[ -z "$next_line" ] && continue` skips empty values to avoid `sed` misbehaving.
- `next_fen=$(sed -n "${next_line}p" "${debug_dir}/fen_eval.txt")` reads the full `fen + Stockfish info` line for that position.
- `[ -n "$next_fen" ] && printf "%s\n" "$next_fen"` prints the line only if it isn't empty.
- `tee "${debug_dir}/puzzles.txt"` writes this game's candidates to `debug/puzzles.txt`.
- `>> "${PUZZLES_FILE:-puzzles.txt}"` appends them to the main `puzzles.txt` (or `$PUZZLES_FILE` if set).
