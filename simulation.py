from loader import load_players
from draft_board import DraftBoard
from draft_engine import DraftEngine
from league import League


class Simulation:

    def __init__(self):

        self.players = load_players()

        self.board = DraftBoard(self.players)

        self.league = League()

        self.engine = DraftEngine(
            self.league,
            self.board,
        )

    def run(self):

        self.engine.run()

        return self.engine