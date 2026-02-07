from random import choice as pick_from
import chess
from boards import SQUARE_SIZE, Board

BOT_DEPTH_PLY = 2


class Player:
    def __init__(self, is_white, live_board, logger):
        self.color = is_white
        self.play_board = live_board
        self.log = logger

        if self.color: self.log("White player created\n")
        else: self.log("Black player created\n")

    def is_my_turn(self):
        if self.play_board.is_game_over():
            self.log("Game Over\n")
            return False
        elif self.play_board.turn == self.color:
            return True
        return False

    def bot_trigger(self, event):
        pass

    def on_click(self, event):
        if self.is_my_turn():
            self.click_board(self.play_board, event.x, event.y)

    def on_analysis_click(self, event):
        pass

    def click_board(self, board, click_x, click_y):
        col = click_x // SQUARE_SIZE
        row = click_y // SQUARE_SIZE
        square = chess.square(col, 7 - row)
        piece = board.piece_at(square)
        piece = piece if piece and piece.color == self.color else None
        if board.selected_square is not None:
            for move in board.legal_moves:
                if move.from_square == board.selected_square \
                        and move.to_square == square:
                    board.play_move(move)
                    break
        board.selected_square = square if piece else None
        board.render()


class HumanPlayer(Player):
    def __init__(self, is_white, live_board, analysis_board, logger):
        super().__init__(is_white, live_board, logger)


class Bot(Player):
    def __init__(self, is_white, live_board, analysis_board, logger):
        super().__init__(is_white, live_board, logger)

        self.analysis_board = analysis_board

        self.move_scores = {}
        self._last_score = 0
        self._search_calls = 0

    # --- Event response ---
    def bot_trigger(self, event):
        if self.is_my_turn():
            self.play_best_move()

    def on_analysis_click(self, event):
        if self.move_scores:
            self.click_board(self.analysis_board, event.x, event.y)

    # --- Finding and playing a move ---
    def get_move_score(self, move, board, depth):
        self._search_calls += 1
        board.push(move)
        if depth == 0:
            best = self.evaluate_pos(board)
        elif board.is_game_over():
            best = 1000 if board.outcome().winner == self.color else -1000
        else:
            best = -1e9 if board.turn == self.color else 1e9
            chooser = max if board.turn == self.color else min
            for next_move in board.legal_moves:
                score = self.get_move_score(next_move, board, depth - 1)
                best = chooser(best, score)
        board.pop()
        return best

    def play_best_move(self):
        self.move_scores = {}
        test_board = Board()
        test_board.set_fen(self.play_board.fen())
        self._search_calls = 0
        for move in self.play_board.legal_moves:
            score = self.get_move_score(move, test_board, BOT_DEPTH_PLY)
            self.move_scores.update({move.uci():score})
        best_move_score = max(self.move_scores.values())
        all_good_moves = [key for key, value in self.move_scores.items()
                          if value == best_move_score]
        best_move = chess.Move.from_uci(pick_from(all_good_moves))

        # Log move search info
        self.log(f"{"White" if self.color else "Black"} bot"
                 + f" picked {self.play_board.san(best_move)} randomly"
                 + f" out of {len(all_good_moves)} considered moves."
                 + f"\n    - It took {self._search_calls} recursions"
                 + f" at depth {BOT_DEPTH_PLY}.\n")
        alog_text = f"{"White" if self.color else "Black"} considered"
        for move in all_good_moves:
            m = chess.Move.from_uci(move)
            m = self.play_board.san(m)
            alog_text += f"\n    - {m}"
        self.log(alog_text, True)

        # Sync the analysis board with the current position minus last move
        relative_scores = {move: score - self._last_score
                           for move, score in self.move_scores.items()}
        self.analysis_board.set_fen(self.play_board.fen())
        self.analysis_board.set_scores(relative_scores)
        self.analysis_board.selected_square = best_move.from_square
        self.analysis_board.render()

        self._last_score = best_move_score
        self.play_board.play_move(best_move)

    # --- Position scoring logic ---
    # Override this method to customize the bot
    def evaluate_pos(self, board):
        mat = board.material_count()
        return mat[self.color] - mat[not self.color]
