from draft_slot_analyzer import DraftSlotAnalyzer


SIMULATIONS_PER_SLOT = 2


def main() -> None:
    print("========================================")
    print("              GRIDIRON AI")
    print("========================================")

    print(
        f"\nComparing all 10 draft slots with "
        f"{SIMULATIONS_PER_SLOT} identical "
        f"market scenarios each...\n"
    )

    analyzer = DraftSlotAnalyzer()

    analysis = analyzer.analyze(
        simulations_per_slot=SIMULATIONS_PER_SLOT,
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
    print("=" * 70)


if __name__ == "__main__":
    main()