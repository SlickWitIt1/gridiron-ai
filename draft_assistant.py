from time import perf_counter

from wait_analyzer import WaitAnalyzer


DEFAULT_SIMULATIONS = 100


def read_integer(
    prompt: str,
    minimum: int,
    maximum: int | None = None,
    default: int | None = None,
) -> int:
    while True:
        default_text = (
            f" [{default}]"
            if default is not None
            else ""
        )

        raw_value = input(
            f"{prompt}{default_text}: "
        ).strip()

        if not raw_value and default is not None:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if value < minimum:
            print(
                f"Please enter a number of at least "
                f"{minimum}."
            )
            continue

        if (
            maximum is not None
            and value > maximum
        ):
            print(
                f"Please enter a number no greater "
                f"than {maximum}."
            )
            continue

        return value


def read_players() -> tuple[str, ...]:
    print()
    print(
        "Enter the players you want to compare."
    )
    print(
        "Separate names with commas."
    )
    print(
        "Example: Josh Allen, Garrett Wilson, "
        "Ladd McConkey"
    )

    while True:
        raw_players = input(
            "\nPlayers: "
        ).strip()

        players = tuple(
            player.strip()
            for player in raw_players.split(",")
            if player.strip()
        )

        if players:
            return players

        print(
            "Please enter at least one player."
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


def print_results(
    results,
    current_pick: int,
    next_pick: int,
    runtime: float,
) -> None:
    print("\n" + "=" * 92)
    print(" GRIDIRON AI — DRAFT NOW OR WAIT?")
    print(
        f" Current pick: {current_pick} | "
        f"Next pick: {next_pick}"
    )
    print("=" * 92)

    print(
        f"{'Player':<26}"
        f"{'Avail Now':>12}"
        f"{'Survives':>12}"
        f"{'Recommendation':>26}"
    )

    print("-" * 92)

    for result in results:
        survival_text = (
            f"{result.survival_probability:.1%}"
            if result.survival_probability
            is not None
            else "N/A"
        )

        print(
            f"{result.player_name:<26}"
            f"{result.available_now_probability:>11.1%}"
            f"{survival_text:>12}"
            f"{recommendation(result.survival_probability):>26}"
        )

    print("-" * 92)
    print(f"Runtime: {runtime:.1f} seconds")


def run_analysis() -> None:
    print("\n" + "=" * 44)
    print("       GRIDIRON AI DRAFT ASSISTANT")
    print("=" * 44)

    draft_slot = read_integer(
        prompt="Your draft slot",
        minimum=1,
        maximum=10,
        default=7,
    )

    current_pick = read_integer(
        prompt="Current overall pick",
        minimum=1,
        maximum=160,
    )

    next_pick = read_integer(
        prompt="Your next overall pick",
        minimum=current_pick + 1,
        maximum=160,
    )

    simulations = read_integer(
        prompt="Number of simulations",
        minimum=10,
        default=DEFAULT_SIMULATIONS,
    )

    player_names = read_players()

    print()
    print(
        f"Running {simulations} counterfactual "
        f"simulations..."
    )

    start_time = perf_counter()

    analyzer = WaitAnalyzer()

    results = analyzer.analyze_players(
        player_names=player_names,
        draft_slot=draft_slot,
        current_pick=current_pick,
        next_pick=next_pick,
        simulations=simulations,
    )

    runtime = perf_counter() - start_time

    print_results(
        results=results,
        current_pick=current_pick,
        next_pick=next_pick,
        runtime=runtime,
    )


def main() -> None:
    while True:
        run_analysis()

        print()
        again = input(
            "Run another comparison? [y/N]: "
        ).strip().lower()

        if again not in {"y", "yes"}:
            print("\nExiting Gridiron AI.")
            break


if __name__ == "__main__":
    main()