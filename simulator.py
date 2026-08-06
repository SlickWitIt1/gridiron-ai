from simulation import Simulation


def main():
    print("===================================")
    print(" Taylor Draft Simulator")
    print("===================================")

    simulation = Simulation()
    engine = simulation.run()

    print(f"\nDraft picks recorded: {len(engine.draft_results)}")

    if engine.draft_results:
        print("\nFirst recorded pick:")
        print(engine.draft_results[0])

        print("\nLast recorded pick:")
        print(engine.draft_results[-1])

    print("\nFINAL ROSTERS")

    for team in simulation.league.teams:
        team.print_roster()


if __name__ == "__main__":
    main()