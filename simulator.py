from loader import load_players
from draft_board import DraftBoard
from draft_engine import DraftEngine
from league import League


def main():

    print("===================================")
    print(" Taylor Draft Simulator")
    print("===================================")

    print("\nLoading players...")

    players = load_players()

    print(f"Loaded {len(players)} players.")

    board = DraftBoard(players)

    league = League()

    engine = DraftEngine(league, board)

    engine.run()

    print("\n\nFINAL ROSTERS")

    for team in league.teams:
        team.print_roster()


if __name__ == "__main__":
    main()