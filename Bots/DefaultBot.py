from src.players import Bot

class DefaultBot(Bot):
    def evaluate_pos(self, board):
        mat = board.material_count()
        return mat[self.color] - mat[not self.color]
