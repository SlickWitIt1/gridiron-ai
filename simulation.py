from draft_board import DraftBoard
from draft_engine import DraftEngine
from league import League
from loader import load_players
from market import DraftMarket
from player import Player
from preferences import load_my_guys


class Simulation:
    def __init__(
        self,
        user_team_number: int = 7,
        seed: int | None = None,
        players: list[Player] | None = None,
        approved_players: set[str] | None = None,
        forbidden_players_by_pick: dict[
            int,
            set[str],
        ] | None = None,
    ):
        self.user_team_number = user_team_number
        self.seed = seed

        self.players = (
            players
            if players is not None
            else load_players()
        )

        self.approved_players = (
            approved_players
            if approved_players is not None
            else load_my_guys()
        )

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
            forbidden_players_by_pick=(
                forbidden_players_by_pick
            ),
        )

    def run(
        self,
        print_picks: bool = True,
        max_overall_pick: int | None = None,
    ) -> DraftEngine:
        self.engine.run(
            print_picks=print_picks,
            max_overall_pick=max_overall_pick,
        )

        return self.engine