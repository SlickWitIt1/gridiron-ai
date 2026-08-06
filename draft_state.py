from dataclasses import dataclass

from draft_board import DraftBoard
from league import League
from market import DraftMarket
from team import Team


@dataclass(slots=True)
class DraftState:
    league: League
    board: DraftBoard
    market: DraftMarket
    user_team_number: int
    current_pick: int = 1

    @property
    def user_team(self) -> Team:
        return self.league.teams[
            self.user_team_number - 1
        ]

    @property
    def available_players(self):
        return self.board.available_players

    @property
    def available_names(self) -> set[str]:
        return self.board.available_names

    @property
    def drafted_player_count(self) -> int:
        return len(self.board.available_names) - len(
            self.available_names
        )

    @property
    def total_picks(self) -> int:
        return len(self.league.draft_order)

    @property
    def current_round(self) -> int:
        return (
            (self.current_pick - 1)
            // self.league.num_teams
        ) + 1

    @property
    def current_team_number(self) -> int | None:
        if not 1 <= self.current_pick <= self.total_picks:
            return None

        return self.league.draft_order[
            self.current_pick - 1
        ]

    @property
    def next_user_pick(self) -> int | None:
        for overall_pick in range(
            self.current_pick + 1,
            self.total_picks + 1,
        ):
            team_number = self.league.draft_order[
                overall_pick - 1
            ]

            if team_number == self.user_team_number:
                return overall_pick

        return None