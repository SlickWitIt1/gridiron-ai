from time import perf_counter

from draft_slot_analyzer import DraftSlotAnalyzer


SIMULATIONS_PER_SLOT = 100

DRAFT_SLOT = 7
CURRENT_PICK = 27
NEXT_PICK = 34

PLAYERS_TO_CHECK = (
    "Josh Allen",
    "Brock Bowers",
    "Kenneth Walker III",
    "Garrett Wilson",
    "Ladd McConkey",
    "Quinshon Judkins",
    "Bucky Irving",
)


def recommendation(
    survival_probability: float | None,
) -> str:
    if survival_probability is None:
        return "Usually gone already"

    if survival_probability < 0.25:
        return "DRAFT NOW"

    if survival_probability < 0.60:
        return "Risky to wait"

    if survival_probability < 0.85:
        return "Probably can wait"

    return "Safe to wait"


def main() -> None:
    print("========================================")
    print("              GRIDIRON AI")
    print("========================================")

    print(
        f"\nRunning {SIMULATIONS_PER_SLOT} "
        f"simulations per draft slot...\n"
    )

    start_time = perf_counter()

    analyzer = DraftSlotAnalyzer()

    analysis = analyzer.analyze(
        simulations_per_slot=SIMULATIONS_PER_SLOT,
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

    print("\n" + "=" * 86)
    print(
        f" SLOT {DRAFT_SLOT}: "
        f"DRAFT NOW OR WAIT?"
    )
    print(
        f" Current pick: {CURRENT_PICK} | "
        f"Next pick: {NEXT_PICK}"
    )
    print("=" * 86)

    print(
        f"{'Player':<24}"
        f"{'Avg Pick':>10}"
        f"{'Avail Now':>12}"
        f"{'Survives':>12}"
        f"{'Recommendation':>24}"
    )

    print("-" * 86)

    availability = analysis.availability_for_slot(
        DRAFT_SLOT
    )

    for player_name in PLAYERS_TO_CHECK:
        average_pick = availability.average_pick(
            player_name
        )

        available_now = (
            availability.probability_available(
                player_name=player_name,
                overall_pick=CURRENT_PICK,
            )
        )

        survival = (
            availability.survival_probability(
                player_name=player_name,
                current_pick=CURRENT_PICK,
                next_pick=NEXT_PICK,
            )
        )

        average_pick_text = (
            f"{average_pick:.1f}"
            if average_pick is not None
            else "N/A"
        )

        survival_text = (
            f"{survival:.1%}"
            if survival is not None
            else "N/A"
        )

        print(
            f"{player_name:<24}"
            f"{average_pick_text:>10}"
            f"{available_now:>11.1%}"
            f"{survival_text:>12}"
            f"{recommendation(survival):>24}"
        )

    print("-" * 86)

    print(
        f"Runtime: {elapsed_seconds:.1f} seconds"
    )


if __name__ == "__main__":
    main()