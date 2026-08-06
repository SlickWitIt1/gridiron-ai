from draft_board import DraftBoard
from draft_engine import DraftEngine
from league import League
from loader import load_players
from preferences import load_my_guys


class Simulation:
    def __init__(self, user_team_number: int = 7):
        self.user_team_number = user_team_number

        self.players = load_players()
        self.approved_players = load_my_guys()

        self.board = DraftBoard(self.players)
        self.league = League()

        self.engine = DraftEngine(
            league=self.league,
            board=self.board,
            user_team_number=self.user_team_number,
            approved_players=self.approved_players,
        )

    def run(self, print_picks: bool = True) -> DraftEngine:
        self.engine.run(print_picks=print_picks)
        return self.engine