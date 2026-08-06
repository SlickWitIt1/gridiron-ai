from draft_board import DraftBoard
from draft_engine import DraftEngine
from league import League
from loader import load_players
from market import DraftMarket
from preferences import load_my_guys


class Simulation:
    def __init__(
        self,
        user_team_number: int = 7,
        seed: int | None = None,
    ):
        self.user_team_number = user_team_number
        self.seed = seed

        self.players = load_players()
        self.approved_players = load_my_guys()

        self.market = DraftMarket(
            players=self.players,
            seed=self.seed,
        )

        self.board = DraftBoard(self.players)
        self.league = League()

        self.engine = DraftEngine(
            league=self.league,
            board=self.board,
            market=self.market,
            user_team_number=self.user_team_number,
            approved_players=self.approved_players,
        )

    def run(self, print_picks: bool = True) -> DraftEngine:
        self.engine.run(print_picks=print_picks)
        return self.engine