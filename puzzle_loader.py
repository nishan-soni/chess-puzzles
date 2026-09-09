"""
Module 1: Puzzle loading.

Reads puzzles.txt where each line is:

    <fen of board> <TAB> <fen after the blundered move> <TAB> <puzzle moves in uci, space separated>

For each line we figure out what move was actually played to get from the
first FEN to the second (the "blunder move") by trying every legal move
from the first position and seeing which one produces the second position.

Promotions are ignored / assumed not to occur, per requirements.
"""

from dataclasses import dataclass, field
from typing import List

import chess


@dataclass
class Puzzle:
    board: str                      # fen before the blunder
    blunder_move: str                # uci move that was played to reach fen_after
    puzzle_moves: List[str] = field(default_factory=list)  # solution moves, uci


def find_blunder_move(fen_before: str, fen_after: str) -> str:
    """Return the uci move played from fen_before that results in fen_after.

    Raises ValueError if no single legal move explains the difference.
    """
    board = chess.Board(fen_before)
    target_piece_placement = chess.Board(fen_after).board_fen()

    for move in board.legal_moves:
        board.push(move)
        if board.board_fen() == target_piece_placement:
            board.pop()
            return move.uci()
        board.pop()

    raise ValueError(
        f"Could not find a legal move from:\n  {fen_before}\nto:\n  {fen_after}"
    )


def load_puzzles(path: str) -> List[Puzzle]:
    """Parse the puzzle file into a list of Puzzle objects."""
    puzzles = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue

            parts = line.split(" <t> ")
            if len(parts) < 3:
                print(f"Skipping malformed line {line_num}: expected 3 tab-separated fields")
                continue

            fen_before, fen_after, moves_str = parts[0].strip(), parts[1].strip(), parts[2].strip()
            puzzle_moves = moves_str.split()
            if not puzzle_moves:
                print(f"Skipping line {line_num}: no puzzle moves found")
                continue

            try:
                blunder_move = find_blunder_move(fen_before, fen_after)
            except ValueError as e:
                print(f"Skipping line {line_num}: {e}")
                continue

            puzzles.append(Puzzle(
                board=fen_before,
                blunder_move=blunder_move,
                puzzle_moves=puzzle_moves,
            ))

    return puzzles


if __name__ == "__main__":
    # Quick manual check when run directly: python3 puzzle_loader.py puzzles.txt
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "puzzles.txt"
    chess = load_puzzles(path)
    print(f"Loaded {len(chess)} puzzle(s)\n")
    for i, p in enumerate(chess, start=1):
        print(f"Puzzle {i}:")
        print(f"  board:        {p.board}")
        print(f"  blunder_move: {p.blunder_move}")
        print(f"  puzzle_moves: {p.puzzle_moves}")
        print()