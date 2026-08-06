from time import perf_counter

from draft_slot_analyzer import (
    DraftSlotAnalyzer,
)


SIMULATIONS_PER_SLOT = 100
AVAILABILITY_PICK = 50

PLAYERS_TO_CHECK = (
    "Josh Allen",
    "Brock Bowers",
    "James Cook III",
    "Tee Higgins",
)


def main() -> None:
    print("========================================")
    print("              GRIDIRON AI")
    print("========================================")

    print(
        f"\nComparing all 10 draft slots with "
        f"{SIMULATIONS_PER_SLOT} identical "
        f"market scenarios each...\n"
    )

    start_time = perf_counter()

    analyzer = DraftSlotAnalyzer()

    analysis = analyzer.analyze(
        simulations_per_slot=(
            SIMULATIONS_PER_SLOT
        ),
    )

    elapsed_seconds = (
        perf_counter() - start_time
    )

    print("\n" + "=" * 103)
    print(" DRAFT SLOT RANKINGS")
    print("=" * 103)

    print(
        f"{'Rank':<6}"
        f"{'Slot':<7}"
        f"{'Starter':>11}"
        f"{'Roster':>11}"
        f"{'My Guys':>10}"
        f"{'Avg Rank':>11}"
        f"{'Surplus':>11}"
        f"{'Best':>11}"
        f"{'Worst':>11}"
    )

    print("-" * 103)

    for ranking, result in enumerate(
        analysis.ranked_results,
        start=1,
    ):
        print(
            f"{ranking:<6}"
            f"{result.draft_slot:<7}"
            f"{result.average_starter_projection:>11.1f}"
            f"{result.average_roster_projection:>11.1f}"
            f"{result.average_my_guys:>10.2f}"
            f"{result.average_roster_rank:>11.1f}"
            f"{result.average_surplus:>11.1f}"
            f"{result.best_starter_projection:>11.1f}"
            f"{result.worst_starter_projection:>11.1f}"
        )

    best = analysis.best_slot

    print("\n" + "=" * 70)
    print(
        f" BEST PROJECTED STARTING LINEUP: "
        f"SLOT {best.draft_slot}"
    )
    print(
        f" Average starter projection: "
        f"{best.average_starter_projection:.1f}"
    )
    print(
        f" Average My Guys: "
        f"{best.average_my_guys:.2f}/16"
    )
    print(
        f" Average roster rank: "
        f"{best.average_roster_rank:.1f}"
    )
    print(
        f" Average surplus: "
        f"{best.average_surplus:+.1f} picks"
    )
    print(
        f" Total runtime: "
        f"{elapsed_seconds:.1f} seconds"
    )
    print("=" * 70)

    print("\n" + "=" * 70)
    print(
        f" PLAYER AVAILABILITY AT "
        f"OVERALL PICK {AVAILABILITY_PICK}"
    )
    print("=" * 70)

    print(
        f"{'Player':<24}"
        f"{'Avg Pick':>12}"
        f"{'Drafted':>12}"
        f"{'Available':>14}"
    )

    print("-" * 70)

    availability = analysis.availability

    for player_name in PLAYERS_TO_CHECK:
        average_pick = (
            availability.average_pick(
                player_name
            )
        )

        draft_rate = (
            availability.draft_rate(
                player_name
            )
        )

        probability = (
            availability.probability_available(
                player_name=player_name,
                overall_pick=(
                    AVAILABILITY_PICK
                ),
            )
        )

        average_pick_text = (
            f"{average_pick:.1f}"
            if average_pick is not None
            else "N/A"
        )

        print(
            f"{player_name:<24}"
            f"{average_pick_text:>12}"
            f"{draft_rate:>11.1%}"
            f"{probability:>13.1%}"
        )

    print("-" * 70)

    print(
        f"Availability database contains "
        f"{availability.simulations} drafts."
    )


if __name__ == "__main__":
    main()