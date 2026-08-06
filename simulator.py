from config import USER_TEAM_NUMBER
from lineup_optimizer import LineupOptimizer
from projection_loader import load_projections
from simulation import Simulation


def print_selection(
    slot: str,
    name: str,
    points: float,
) -> None:
    print(
        f"{slot:<5} | "
        f"{name:<25} | "
        f"{points:>6.1f}"
    )


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

    optimizer = LineupOptimizer(projections)
    lineup = optimizer.optimize(user_team)

    print("\n===================================")
    print(f" STARTING LINEUP — SLOT {USER_TEAM_NUMBER}")
    print("===================================\n")

    for selection in lineup.starters:
        print_selection(
            slot=selection.slot,
            name=selection.player.name,
            points=selection.projected_points,
        )

    print("\n" + "-" * 48)

    print(
        f"Projected starter points: "
        f"{lineup.starter_projection:.1f}"
    )

    print("\n===================================")
    print(" BENCH")
    print("===================================\n")

    for selection in lineup.bench:
        print_selection(
            slot=selection.slot,
            name=selection.player.name,
            points=selection.projected_points,
        )

    print("\n" + "-" * 48)

    print(
        f"Projected bench points: "
        f"{lineup.bench_projection:.1f}"
    )

    print(
        f"Total roster projection: "
        f"{lineup.starter_projection + lineup.bench_projection:.1f}"
    )

    print(
        f"Starting lineup players: "
        f"{len(lineup.starters)}/9"
    )

    print(
        f"Bench players: "
        f"{len(lineup.bench)}/7"
    )

    print(
        f"Draft picks recorded: "
        f"{len(engine.draft_results)}"
    )


if __name__ == "__main__":
    main()