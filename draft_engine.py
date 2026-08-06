from draft_board import DraftBoard
from draft_pick import DraftPick
from decision_engine import DecisionEngine
from league import League


class DraftEngine:
    def __init__(self, league: League, board: DraftBoard):
        self.league = league
        self.board = board
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

            player = self.decision_engine.choose_player(
                team,
                self.board.available_players,
            )

            if player is None:
                break

            team.add_player(player)
            self.board.draft_player(player)

            round_number = (
                (overall_pick - 1) // self.league.num_teams
            ) + 1

            pick_in_round = (
                (overall_pick - 1) % self.league.num_teams
            ) + 1

            draft_pick = DraftPick(
                overall=overall_pick,
                round_number=round_number,
                pick_in_round=pick_in_round,
                team_number=team_number,
                player=player,
            )

            self.draft_results.append(draft_pick)

            if print_picks:
                print(draft_pick)

        if print_picks:
            print("\n==============================")
            print("      DRAFT COMPLETE")
            print("==============================")

        return self.draft_results