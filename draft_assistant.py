from time import perf_counter

from projection_loader import load_projections
from recommendation_engine import (
    RecommendationEngine,
)
from team import Team
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


def read_player_names(
    heading: str,
    example: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    print()
    print(heading)
    print(
        "Separate names with commas."
    )
    print(
        f"Example: {example}"
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

        if players or allow_empty:
            return players

        print(
            "Please enter at least one player."
        )


def build_user_team(
    player_names: tuple[str, ...],
    wait_analyzer: WaitAnalyzer,
    draft_slot: int,
) -> Team:
    team = Team(draft_slot)

    missing_players: list[str] = []

    for player_name in player_names:
        player = next(
            (
                candidate
                for candidate
                in wait_analyzer.players
                if (
                    candidate.name.strip().lower()
                    == player_name.strip().lower()
                )
            ),
            None,
        )

        if player is None:
            missing_players.append(
                player_name
            )
            continue

        try:
            team.add_player(player)

        except ValueError as error:
            print()
            print(
                f"Could not add {player.name}: "
                f"{error}"
            )

    if missing_players:
        print()
        print(
            "The following roster names "
            "were not recognized:"
        )

        for player_name in missing_players:
            print(
                f"- {player_name}"
            )

    return team


def print_roster_summary(
    team: Team,
) -> None:
    print("\n" + "=" * 54)
    print(" CURRENT ROSTER")
    print("=" * 54)

    if not team.players:
        print(
            "No players drafted yet."
        )

    else:
        for player in team.players:
            print(
                f"{player.position:<5} | "
                f"{player.name}"
            )

    print("-" * 54)

    print(
        f"QB: {team.count_position('QB')} | "
        f"RB: {team.count_position('RB')} | "
        f"WR: {team.count_position('WR')} | "
        f"TE: {team.count_position('TE')} | "
        f"DST: {team.count_position('DST')} | "
        f"K: {team.count_position('K')}"
    )

    print(
        f"Players drafted: "
        f"{len(team.players)}/16"
    )

    print(
        f"Starter slots filled: "
        f"{team.starter_slots_filled()}/9"
    )


def print_recommendations(
    recommendations,
    current_pick: int,
    next_pick: int,
    runtime: float,
) -> None:
    print("\n" + "=" * 116)
    print(
        " GRIDIRON AI — "
        "ROSTER-AWARE RECOMMENDATIONS"
    )

    print(
        f" Current pick: {current_pick} | "
        f"Next pick: {next_pick}"
    )

    print("=" * 116)

    print(
        f"{'Rank':<6}"
        f"{'Player':<25}"
        f"{'Pos':<6}"
        f"{'Score':>8}"
        f"{'Grade':>8}"
        f"{'Roster':>10}"
        f"{'Survives':>12}"
        f"{'Action':>24}"
    )

    print("-" * 116)

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
            f"{recommendation.roster_fit_score:>+10.1f}"
            f"{survival_text:>12}"
            f"{recommendation.action:>24}"
        )

    print("-" * 116)

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

    print("\n" + "=" * 116)

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

    print("=" * 116)

    for reason in top_recommendation.reasons:
        print(
            f"- {reason}"
        )


def run_analysis() -> None:
    print("\n" + "=" * 52)
    print(
        "            GRIDIRON AI "
        "DRAFT ASSISTANT"
    )
    print("=" * 52)

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

    roster_names = read_player_names(
        heading=(
            "Enter the players already "
            "on your roster."
        ),
        example=(
            "CeeDee Lamb, Brock Bowers"
        ),
        allow_empty=True,
    )

    candidate_names = read_player_names(
        heading=(
            "Enter the available players "
            "you want ranked."
        ),
        example=(
            "Josh Allen, Garrett Wilson, "
            "Ladd McConkey"
        ),
    )

    print()

    print(
        f"Running {simulations} "
        f"counterfactual simulations "
        f"and ranking "
        f"{len(candidate_names)} players..."
    )

    start_time = perf_counter()

    wait_analyzer = WaitAnalyzer()

    user_team = build_user_team(
        player_names=roster_names,
        wait_analyzer=wait_analyzer,
        draft_slot=draft_slot,
    )

    wait_results = (
        wait_analyzer.analyze_players(
            player_names=candidate_names,
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
            wait_results=wait_results,
            user_team=user_team,
        )
    )

    runtime = (
        perf_counter()
        - start_time
    )

    print_roster_summary(
        user_team
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