from config import USER_TEAM_NUMBER
from roster_evaluator import RosterEvaluator
from simulation import Simulation


def main():

    print("===================================")
    print("      GRIDIRON AI")
    print("===================================")

    simulation = Simulation(
        user_team_number=USER_TEAM_NUMBER,
    )

    engine = simulation.run(print_picks=True)

    team = simulation.league.teams[
        USER_TEAM_NUMBER - 1
    ]

    evaluator = RosterEvaluator()

    results = evaluator.evaluate(team)

    print("\n")
    print("=" * 35)
    print(" GRIDIRON REPORT")
    print("=" * 35)

    print(f"Overall Score : {results['overall']}")
    print()

    print(f"QB : {results['QB']}")
    print(f"RB : {results['RB']}")
    print(f"WR : {results['WR']}")
    print(f"TE : {results['TE']}")
    print(f"DST: {results['DST']}")
    print(f"K  : {results['K']}")

    print("\n")
    print("=" * 35)
    print(" YOUR ROSTER")
    print("=" * 35)

    team.print_roster()

    print(f"\nDraft Picks Recorded: {len(engine.draft_results)}")


if __name__ == "__main__":
    main()