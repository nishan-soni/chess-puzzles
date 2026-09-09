"""
Module 1: Puzzle loading.

Reads puzzle candidates where each line is a Stockfish info string
containing a FEN and a principal variation:

    <fen of board> info ... pv <uci moves ...>

For each line we extract the FEN (everything before "info") and the
UCI moves (everything after "pv").
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Puzzle:
    board: str                      # fen to show
    blunder_move: str = ""          # no longer tracked
    puzzle_moves: List[str] = field(default_factory=list)  # solution moves, uci


def load_puzzles(path: str) -> List[Puzzle]:
    """Parse the puzzle file into a list of Puzzle objects."""
    puzzles = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue

            fen = line.split("info", 1)[0].strip()
            if not fen:
                print(f"Skipping malformed line {line_num}: no FEN found")
                continue

            parts = line.split(" pv ", 1)
            if len(parts) < 2:
                print(f"Skipping line {line_num}: no pv moves found")
                continue

            puzzle_moves = parts[1].strip().split()
            if not puzzle_moves:
                print(f"Skipping line {line_num}: no pv moves found")
                continue

            puzzles.append(Puzzle(
                board=fen,
                blunder_move="",
                puzzle_moves=puzzle_moves,
            ))

    return puzzles


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/puzzles.txt"
    puzzles = load_puzzles(path)
    print(f"Loaded {len(puzzles)} puzzle(s)\n")
    for i, p in enumerate(puzzles):
        print(f"Puzzle {i}:")
        print(f"  board:        {p.board}")
        print(f"  puzzle_moves: {p.puzzle_moves}")
        print()
