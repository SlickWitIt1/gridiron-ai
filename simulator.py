from config import USER_TEAM_NUMBER
from preferences import normalize_name
from projection_loader import load_projections
from simulation import Simulation


def main() -> None:
    print("===================================")
    print("           GRIDIRON AI")
    print("===================================")

    projections = load_projections()

    print(
        f"\nPlayer projections loaded: "
        f"{len(projections)}"
    )

    simulation = Simulation(
        user_team_number=USER_TEAM_NUMBER,
    )

    engine = simulation.run(print_picks=False)

    user_team = simulation.league.teams[
        USER_TEAM_NUMBER - 1
    ]

    print("\n===================================")
    print(f" YOUR ROSTER — DRAFT SLOT {USER_TEAM_NUMBER}")
    print("===================================\n")

    total_roster_projection = 0.0
    players_with_projections = 0
    missing_players: list[str] = []

    for player in user_team.players:
        projection = projections.get(
            normalize_name(player.name)
        )

        if projection is None:
            missing_players.append(player.name)
            print(
                f"{player.position:<4} | "
                f"{player.name:<25} | "
                f"No projection"
            )
            continue

        players_with_projections += 1
        total_roster_projection += projection.fantasy_points

        print(projection)

    print("\n" + "-" * 55)

    print(
        f"Players with projections: "
        f"{players_with_projections}/"
        f"{len(user_team.players)}"
    )

    print(
        f"Total 16-player projection: "
        f"{total_roster_projection:.1f}"
    )

    print(
        f"Draft picks recorded: "
        f"{len(engine.draft_results)}"
    )

    if missing_players:
        print("\nMissing projections:")

        for name in missing_players:
            print(f"- {name}")


if __name__ == "__main__":
    main()