from preferences import normalize_name
from simulation import Simulation


USER_TEAM_NUMBER = 7


def main():
    print("===================================")
    print(" Taylor Draft Simulator")
    print("===================================")

    simulation = Simulation(
        user_team_number=USER_TEAM_NUMBER,
    )

    engine = simulation.run(print_picks=True)

    user_team = simulation.league.teams[
        USER_TEAM_NUMBER - 1
    ]

    print("\n===================================")
    print(f" YOUR ROSTER — DRAFT SLOT {USER_TEAM_NUMBER}")
    print("===================================\n")

    approved_count = 0

    for player in user_team.players:
        is_approved = (
            normalize_name(player.name)
            in simulation.approved_players
        )

        if is_approved:
            approved_count += 1

        print(player)

    print(
        f"\nMy Guys drafted: "
        f"{approved_count}/{len(user_team.players)}"
    )

    print(
        f"Draft picks recorded: "
        f"{len(engine.draft_results)}"
    )


if __name__ == "__main__":
    main()