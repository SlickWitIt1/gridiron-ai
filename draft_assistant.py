from time import perf_counter

from projection_loader import load_projections
from recommendation_engine import (
    RecommendationEngine,
)
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

        if (
            not raw_value
            and default is not None
        ):
            return default

        try:
            value = int(raw_value)

        except ValueError:
            print(
                "Please enter a whole number."
            )
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
        "Enter the available players "
        "you want ranked."
    )

    print(
        "Separate names with commas."
    )

    print(
        "Example: Josh Allen, "
        "Garrett Wilson, Ladd McConkey"
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


def print_recommendations(
    recommendations,
    current_pick: int,
    next_pick: int,
    runtime: float,
) -> None:
    print("\n" + "=" * 104)
    print(
        " GRIDIRON AI — RECOMMENDATIONS"
    )

    print(
        f" Current pick: {current_pick} | "
        f"Next pick: {next_pick}"
    )

    print("=" * 104)

    print(
        f"{'Rank':<6}"
        f"{'Player':<25}"
        f"{'Pos':<6}"
        f"{'Score':>8}"
        f"{'Grade':>8}"
        f"{'Survives':>12}"
        f"{'Action':>22}"
    )

    print("-" * 104)

    for rank, recommendation in enumerate(
        recommendations,
        start=1,
    ):
        survival_text = (
            f"{recommendation.survival_probability:.1%}"
            if recommendation.survival_probability
            is not None
            else "N/A"
        )

        print(
            f"{rank:<6}"
            f"{recommendation.player_name:<25}"
            f"{recommendation.position:<6}"
            f"{recommendation.score:>8.1f}"
            f"{recommendation.grade:>8}"
            f"{survival_text:>12}"
            f"{recommendation.action:>22}"
        )

    print("-" * 104)

    print(
        f"Runtime: {runtime:.1f} seconds"
    )

    if not recommendations:
        print()
        print(
            "No recommendations were produced."
        )

        print(
            "Check the player names and confirm "
            "projection data exists."
        )

        return

    top_recommendation = recommendations[0]

    print("\n" + "=" * 104)

    print(
        f" TOP PICK: "
        f"{top_recommendation.player_name} "
        f"({top_recommendation.position})"
    )

    print(
        f" Grade: "
        f"{top_recommendation.grade} | "
        f"Score: "
        f"{top_recommendation.score:.1f} | "
        f"Action: "
        f"{top_recommendation.action}"
    )

    print("=" * 104)

    for reason in top_recommendation.reasons:
        print(f"- {reason}")


def run_analysis() -> None:
    print("\n" + "=" * 48)
    print(
        "          GRIDIRON AI "
        "DRAFT ASSISTANT"
    )
    print("=" * 48)

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
        f"Running {simulations} "
        f"counterfactual simulations "
        f"and ranking "
        f"{len(player_names)} players..."
    )

    start_time = perf_counter()

    wait_analyzer = WaitAnalyzer()

    wait_results = (
        wait_analyzer.analyze_players(
            player_names=player_names,
            draft_slot=draft_slot,
            current_pick=current_pick,
            next_pick=next_pick,
            simulations=simulations,
        )
    )

    recommendation_engine = (
        RecommendationEngine(
            players=wait_analyzer.players,
            projections=load_projections(),
            approved_players=(
                wait_analyzer
                .approved_players
            ),
        )
    )

    recommendations = (
        recommendation_engine.recommend(
            wait_results
        )
    )

    runtime = (
        perf_counter()
        - start_time
    )

    print_recommendations(
        recommendations=recommendations,
        current_pick=current_pick,
        next_pick=next_pick,
        runtime=runtime,
    )


def main() -> None:
    while True:
        run_analysis()

        print()

        again = input(
            "Run another recommendation? "
            "[y/N]: "
        ).strip().lower()

        if again not in {
            "y",
            "yes",
        }:
            print(
                "\nExiting Gridiron AI."
            )

            break


if __name__ == "__main__":
    main()