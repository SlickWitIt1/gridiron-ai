from league import League
from draft_board import DraftBoard


class DraftEngine:

    def __init__(self, league: League, board: DraftBoard):

        self.league = league
        self.board = board

    def run(self):

        print("\n==============================")
        print("      STARTING DRAFT")
        print("==============================\n")

        overall_pick = 1

        for team_number in self.league.draft_order:

            team = self.league.teams[team_number - 1]

            player = self.board.best_available()

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