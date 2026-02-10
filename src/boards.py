import math

import chess
import tkinter as tk

PIECES = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}
LIGHT_SQ = "#F0D9B5"
DARK_SQ = "#B58863"


class Board(chess.Board):
    def __init__(self):
        super().__init__()

    def material_count(self, piece_values=None):
        if piece_values is None:
            piece_values = {chess.PAWN: 1,
                            chess.KNIGHT: 2.5,
                            chess.BISHOP: 3,
                            chess.ROOK: 5,
                            chess.QUEEN: 10}
        white_mat_count = 0
        black_mat_count = 0
        for piece_type in piece_values.keys():
            piece_squares = self.pieces(piece_type, chess.WHITE)
            white_mat_count += piece_values[piece_type] * len(piece_squares)
            piece_squares = self.pieces(piece_type, chess.BLACK)
            black_mat_count += piece_values[piece_type] * len(piece_squares)
        return {chess.WHITE:white_mat_count, chess.BLACK:black_mat_count}


class LiveBoard(Board):
    def __init__(self,
                 parent,
                 square_size,
                 col,
                 label=("Live Board", 25),
                 padding=0
        ):
        super().__init__()
        self.selected_square = None
        self.size = int(square_size * 8)
        self.square_size = square_size
        self.eval_height = label[1]

        # --- Rendering ---
        frame = tk.Frame(parent)
        frame.grid(row=0, column=col, padx=padding, pady=padding)

        tk.Label(
            frame, text=label[0],
            anchor="center",
            font=("Arial", label[1])
        ).grid(row=0, column=0, padx=padding)

        self.surface = tk.Canvas(
            frame, width=self.size, height=self.size,
            bg="lightgray", highlightthickness=1, highlightbackground="black"
        )
        self.surface.grid(row=1, column=0, padx=padding)

        self.eval_canvas = tk.Canvas(frame,
                                     width=self.size,
                                     height=label[1],
                                     bg="black",
                                     highlightthickness=1,
                                     highlightbackground="gray")
        self.eval_canvas.grid()
        self.eval_fill = self.eval_canvas.create_rectangle(0,
                                                           0,
                                                           self.size/2,
                                                           self.eval_height,
                                                           fill="white", outline="")
        self.eval_text = self.eval_canvas.create_text(self.size // 2,
                                                      self.eval_height // 2,
                                                      text=" ", fill="white")

        self.render()

    def play_move(self, move):
        if move in self.legal_moves:
            self.push(move)
            mat = self.material_count()
            self.set_eval_bar(mat[chess.WHITE] - mat[chess.BLACK])
            self.render()

    def set_eval_bar(self, evaluation):
        fill_percent = 1 - (0.519615 * math.pow(0.832683, evaluation))
        fill_percent = max(0, min(1, fill_percent))

        self.eval_canvas.coords(self.eval_fill,
                                0, 0,
                                int(self.size * fill_percent),
                                self.eval_height)
        text = "      ±0"
        if evaluation > 0:
            text = f"+{abs(evaluation)}      "
        elif evaluation < 0:
            text = f"      -{abs(evaluation)}"
        text_color = "black" if evaluation > 0 else "white"
        self.eval_canvas.itemconfig(self.eval_text, text=text)
        self.eval_canvas.itemconfig(self.eval_text, fill=text_color)

    def reset_game(self):
        super().reset()
        self.set_eval_bar(0)

    def render(self):
        # Draw the board and pieces
        self.surface.delete("all")
        for row in range(8):
            for col in range(8):
                self.surface.create_rectangle(
                    col * self.square_size,
                    row * self.square_size,
                    col * self.square_size + self.square_size,
                    row * self.square_size + self.square_size,
                    fill=LIGHT_SQ if (row + col) % 2 != 0 else DARK_SQ,
                    outline=""
                )
                square = chess.square(col, 7 - row)
                piece = self.piece_at(square)
                if piece:
                    self.surface.create_text(
                        col * self.square_size + self.square_size // 2,
                        row * self.square_size + self.square_size // 2,
                        text=PIECES[piece.symbol()],
                        font=("Arial", 36)
                    )
        # Draw selection box
        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            self.surface.create_rectangle(
                col * self.square_size,
                row * self.square_size,
                (col + 1) * self.square_size,
                (row + 1) * self.square_size,
                outline="#444444",
                width=3
            )

            # Draw legal moves for selected piece
            legal_moves_for_piece = [
                move for move in self.legal_moves
                if move.from_square == self.selected_square
            ]
            for move in legal_moves_for_piece:
                col = chess.square_file(move.to_square)
                row = 7 - chess.square_rank(move.to_square)

                cx = col * self.square_size + self.square_size // 2
                cy = row * self.square_size + self.square_size // 2

                if self.piece_at(move.to_square):
                    r = self.square_size // 3
                    self.surface.create_oval(
                        cx - r, cy - r,
                        cx + r, cy + r,
                        outline="#0F0F0F",
                        width=2,
                    )
                else:
                    r = self.square_size // 10
                    self.surface.create_oval(
                        cx - r, cy - r,
                        cx + r, cy + r,
                        fill="#000000",
                        outline="",
                        stipple="gray50"
                    )


class AnalysisBoard(LiveBoard):
    def __init__(self,
                 parent,
                 square_size,
                 col,
                 label=("Analysis Board", 13),
                 padding=0
        ):
        super().__init__(parent, square_size, col, label, padding)
        self.scores = {}

    def set_scores(self, move_scores):
        self.scores = move_scores

    def render(self):
        super().render()
        if self.selected_square is not None:
            # Get legal moves for selected piece
            legal_moves_for_piece = [
                move for move in self.legal_moves
                if move.from_square == self.selected_square
            ]
            for move in legal_moves_for_piece:
                if move.uci() in self.scores.keys():
                    col = chess.square_file(move.to_square)
                    row = 7 - chess.square_rank(move.to_square)

                    # Render the score for this move
                    clamped_score = max(-3, min(3, self.scores[move.uci()]))
                    color = "#{:02x}{:02x}00".format(int(255 * (1 - clamped_score / 3) / 2),
                                                     int(255 * (1 + clamped_score / 3) / 2))
                    self.surface.create_text(
                        col * self.square_size + 16,
                        row * self.square_size + 12,
                        text=self.scores[move.uci()],
                        font=("Helvetica", 12, "bold"),
                        fill=color
                    )

    def play_move(self, move):
        pass
