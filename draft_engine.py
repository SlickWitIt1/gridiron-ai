from decision_engine import DecisionEngine
from draft_board import DraftBoard
from league import League


class DraftEngine:

    def __init__(self, league: League, board: DraftBoard):

        self.league = league
        self.board = board
        self.decision_engine = DecisionEngine()

    def run(self):

        print("\n==============================")
        print("      STARTING DRAFT")
        print("==============================\n")

        overall_pick = 1

        for team_number in self.league.draft_order:

            team = self.league.teams[team_number - 1]

            player = self.decision_engine.choose_player(
                team,
                self.board.available_players,
            )

            if player is None:
                break

            team.add_player(player)
            self.board.draft_player(player)

            print(
                f"Pick {overall_pick:>3} | "
                f"Team {team_number:>2} | "
                f"{player}"
            )

            overall_pick += 1

        print("\n==============================")
        print("     DRAFT COMPLETE")
        print("==============================")