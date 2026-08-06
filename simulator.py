from time import perf_counter

from wait_analyzer import WaitAnalyzer


DRAFT_SLOT = 7
CURRENT_PICK = 27
NEXT_PICK = 34
SIMULATIONS = 100

PLAYERS_TO_CHECK = (
    "Josh Allen",
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
        f"\nCounterfactual wait analysis\n"
        f"Draft slot: {DRAFT_SLOT}\n"
        f"Current pick: {CURRENT_PICK}\n"
        f"Next pick: {NEXT_PICK}\n"
        f"Simulations: {SIMULATIONS}\n"
    )

    start_time = perf_counter()

    analyzer = WaitAnalyzer()

    print("=" * 86)
    print(" DRAFT NOW OR WAIT?")
    print("=" * 86)

    print(
        f"{'Player':<24}"
        f"{'Avail Now':>12}"
        f"{'Survives':>12}"
        f"{'Recommendation':>24}"
    )

    print("-" * 86)

    for player_name in PLAYERS_TO_CHECK:
        result = analyzer.analyze(
            player_name=player_name,
            draft_slot=DRAFT_SLOT,
            current_pick=CURRENT_PICK,
            next_pick=NEXT_PICK,
            simulations=SIMULATIONS,
        )

        survival_text = (
            f"{result.survival_probability:.1%}"
            if result.survival_probability
            is not None
            else "N/A"
        )

        print(
            f"{player_name:<24}"
            f"{result.available_now_probability:>11.1%}"
            f"{survival_text:>12}"
            f"{recommendation(result.survival_probability):>24}"
        )

    elapsed_seconds = (
        perf_counter() - start_time
    )

    print("-" * 86)
    print(
        f"Runtime: {elapsed_seconds:.1f} seconds"
    )


if __name__ == "__main__":
    main()