from preferences import load_my_guys, normalize_name
from simulation import Simulation


def main():
    print("===================================")
    print(" Taylor Draft Simulator")
    print("===================================")

    my_guys = load_my_guys()

    print(f"\nApproved players loaded: {len(my_guys)}")

    simulation = Simulation()
    engine = simulation.run()

    print(f"\nDraft picks recorded: {len(engine.draft_results)}")

    drafted_my_guys = [
        draft_pick
        for draft_pick in engine.draft_results
        if normalize_name(draft_pick.player.name) in my_guys
    ]

    print(
        "Approved players drafted by the league: "
        f"{len(drafted_my_guys)}"
    )

    if engine.draft_results:
        print("\nFirst recorded pick:")
        print(engine.draft_results[0])

        print("\nLast recorded pick:")
        print(engine.draft_results[-1])


if __name__ == "__main__":
    main()