"""
Module 3 (Textual version): Board rendering + click-to-move.

Draws a chess board using Textual with rank numbers (1-8) on the left,
file letters (a-h) on the bottom, and a top bar showing which side is
to move. Click a piece to select it, then click a destination square
to play the next solution move.
"""

import sys

import chess
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static

from puzzle_loader import load_puzzles, Puzzle

UNICODE_PIECES = {
    chess.PAWN: "\u2659",
    chess.KNIGHT: "\u2658",
    chess.BISHOP: "\u2657",
    chess.ROOK: "\u2656",
    chess.QUEEN: "\u2655",
    chess.KING: "\u2654",
}

FILES = "abcdefgh"

WHITE_PIECE_COLOR = "#ffffff"
BLACK_PIECE_COLOR = "#000000"
LIGHT_SQUARE_BG = "#C4A484"
DARK_SQUARE_BG = "#BB9672"
SELECTED_BG = "#c9982e"


class Square(Static, can_focus=False):
    """A single, clickable square on the board."""

    def __init__(self, square_name: str, is_light: bool):
        super().__init__(id=f"square-{square_name}")
        self.square_name = square_name
        self.is_light = is_light
        self.content_text = ""
        self.piece = None
        self.selected = False

    def render(self) -> str:
        return self.content_text

    def set_piece(self, piece):
        self.piece = piece
        if piece is None:
            self.content_text = ""
        else:
            glyph = UNICODE_PIECES[piece.piece_type]
            color = WHITE_PIECE_COLOR if piece.color == chess.WHITE else BLACK_PIECE_COLOR
            self.content_text = f"[{color}]{glyph}[/]"
        self._refresh_style()

    def set_selected(self, selected: bool):
        self.selected = selected
        self._refresh_style()

    def _refresh_style(self):
        if self.selected:
            self.styles.background = SELECTED_BG
        else:
            self.styles.background = LIGHT_SQUARE_BG if self.is_light else DARK_SQUARE_BG
        self.refresh()

    def on_click(self) -> None:
        self.app.on_square_clicked(self.square_name)


class BoardLabel(Static):
    """File/rank label around the board."""

    def __init__(self, text: str):
        super().__init__(text, classes="label")


class BoardView(Container):
    """9x9 grid with rank labels on the left, file labels on the bottom."""

    def compose(self) -> ComposeResult:
        for row in range(8):
            rank = 8 - row
            yield BoardLabel(str(rank))
            for col in range(8):
                file_ch = FILES[col]
                square_name = f"{file_ch}{rank}"
                is_light = (row + col) % 2 == 0
                yield Square(square_name, is_light)

        yield Static("", classes="label corner")
        for file_ch in FILES:
            yield BoardLabel(file_ch)

    def show_board(self, board: chess.Board):
        for square_widget in self.query(Square):
            square = chess.parse_square(square_widget.square_name)
            piece = board.piece_at(square)
            square_widget.set_piece(piece)

    def set_selected_square(self, square_name):
        for square_widget in self.query(Square):
            square_widget.set_selected(square_widget.square_name == square_name)


class PuzzleState:
    """Tracks progress through a single puzzle: the live board, which
    solution move comes next, and the currently-selected square."""

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.board = chess.Board(puzzle.board)
        self.move_index = 0
        self.selected_square = None
        self.solved = self.move_index >= len(puzzle.puzzle_moves)

    def try_move(self, src: str, dst: str) -> str:
        """Attempt src -> dst. Returns a status message."""
        played = src + dst
        expected = self.puzzle.puzzle_moves[self.move_index]

        if played != expected[:4]:
            return ""

        self.board.push(chess.Move.from_uci(expected))
        self.move_index += 1

        if self.move_index >= len(self.puzzle.puzzle_moves):
            self.solved = True
            return "Solved!"

        opponent_move = self.puzzle.puzzle_moves[self.move_index]
        self.board.push(chess.Move.from_uci(opponent_move))
        self.move_index += 1

        if self.move_index >= len(self.puzzle.puzzle_moves):
            self.solved = True
            return "Solved!"

        return ""


class ChessPuzzleApp(App):
    CSS = """
    BoardView {
        layout: grid;
        grid-size: 9 9;
        width: 36;
        height: 18;
        align: center middle;
    }

    Square {
        content-align: center middle;
        width: 100%;
        height: 100%;
    }

    .label {
        content-align: center middle;
        color: #000000;
        width: 100%;
        height: 100%;
    }

    #turn {
        content-align: center middle;
        text-align: center;
        height: 1;
        width: 100%;
    }

    #status {
        color: #000000;
        text-align: center;
        height: 1;
        width: 100%;
    }

    Vertical {
        align: center middle;
        height: auto;
        width: auto;
    }

    Screen {
        align: center middle;
        background: transparent;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "next_puzzle", "Next puzzle"),
        ("r", "reset_puzzle", "Reset puzzle"),
    ]

    def __init__(self, puzzles: list[Puzzle]):
        super().__init__()
        self.puzzles = puzzles
        self.puzzle_index = 0
        self.state = PuzzleState(self.puzzles[self.puzzle_index])
        self._advance_timer = None
        self.ansi_color = True

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("", id="turn")
            yield BoardView()
            yield Static("", id="status")

    def on_mount(self):
        self.refresh_board()

    def _set_status(self, message: str):
        self.query_one("#status").update(message)

    def _refresh_turn(self):
        turn = self.query_one("#turn")
        turn.styles.color = "#000000"
        if self.state.board.turn == chess.WHITE:
            turn.update("White to move")
        else:
            turn.update("Black to move")

    def refresh_board(self):
        board_view = self.query_one(BoardView)
        board_view.show_board(self.state.board)
        board_view.set_selected_square(self.state.selected_square)
        self._refresh_turn()

    def load_puzzle(self, index: int):
        self.puzzle_index = index
        self.state = PuzzleState(self.puzzles[self.puzzle_index])
        self._set_status("")
        self.refresh_board()

    def _next_puzzle(self):
        self._advance_timer = None
        next_index = self.puzzle_index + 1
        if next_index >= len(self.puzzles):
            self._set_status("No more puzzles")
            return
        self.load_puzzle(next_index)

    def _schedule_next(self):
        self._advance_timer = self.set_timer(1.0, self._next_puzzle)
        self._set_status("Solved!")

    def action_next_puzzle(self):
        if self._advance_timer is not None:
            self._advance_timer.stop()
            self._advance_timer = None
        self._next_puzzle()

    def action_reset_puzzle(self):
        if self._advance_timer is not None:
            self._advance_timer.stop()
            self._advance_timer = None
        self.state = PuzzleState(self.puzzles[self.puzzle_index])
        self._set_status("")
        self.refresh_board()

    def on_square_clicked(self, square_name: str):
        state = self.state

        if state.solved:
            if self._advance_timer is not None:
                self._advance_timer.stop()
                self._advance_timer = None
            self._next_puzzle()
            return

        if self._advance_timer is not None:
            return

        if state.selected_square is None:
            square = chess.parse_square(square_name)
            if state.board.piece_at(square) is not None:
                state.selected_square = square_name
        else:
            if square_name == state.selected_square:
                state.selected_square = None
            else:
                src = state.selected_square
                state.selected_square = None
                message = state.try_move(src, square_name)
                if message:
                    self._set_status(message)

        self.refresh_board()

        if state.solved:
            self._schedule_next()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/puzzles.txt"
    puzzles = load_puzzles(path)
    if not puzzles:
        print(f"No puzzles found in {path}")
        sys.exit(1)

    app = ChessPuzzleApp(puzzles)
    app.run()


if __name__ == "__main__":
    main()
