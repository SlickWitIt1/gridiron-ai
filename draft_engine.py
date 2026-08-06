from draft_board import DraftBoard
from draft_pick import DraftPick
from decision_engine import DecisionEngine
from league import League


class DraftEngine:
    def __init__(
        self,
        league: League,
        board: DraftBoard,
        user_team_number: int = 7,
        approved_players: set[str] | None = None,
    ):
        self.league = league
        self.board = board
        self.user_team_number = user_team_number
        self.approved_players = approved_players

        self.decision_engine = DecisionEngine()
        self.draft_results: list[DraftPick] = []

    def run(self, print_picks: bool = True) -> list[DraftPick]:
        self.draft_results = []

        if print_picks:
            print("\n==============================")
            print("      STARTING DRAFT")
            print("==============================\n")

        for overall_pick, team_number in enumerate(
            self.league.draft_order,
            start=1,
        ):
            team = self.league.teams[team_number - 1]

            current_round = (
                (overall_pick - 1) // self.league.num_teams
            ) + 1

            team_approved_players = None

            if team_number == self.user_team_number:
                team_approved_players = self.approved_players

            player = self.decision_engine.choose_player(
                team=team,
                available_players=self.board.available_players,
                current_round=current_round,
                approved_players=team_approved_players,
            )

            if player is None:
                raise RuntimeError(
                    f"Team {team_number} had no eligible player "
                    f"available at overall pick {overall_pick}."
                )

            team.add_player(player)
            self.board.draft_player(player)

            pick_in_round = (
                (overall_pick - 1) % self.league.num_teams
            ) + 1

            draft_pick = DraftPick(
                overall=overall_pick,
                round_number=current_round,
                pick_in_round=pick_in_round,
                team_number=team_number,
                player=player,
            )

            self.draft_results.append(draft_pick)

            if print_picks:
                marker = (
                    "  <-- YOUR PICK"
                    if team_number == self.user_team_number
                    else ""
                )

                print(f"{draft_pick}{marker}")

        if print_picks:
            print("\n==============================")
            print("      DRAFT COMPLETE")
            print("==============================")

        return self.draft_results