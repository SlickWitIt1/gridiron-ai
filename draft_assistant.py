from time import perf_counter

from live_draft import LiveDraftSession
from preferences import normalize_name
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


def read_player_names(
    heading: str,
) -> tuple[str, ...]:
    print()
    print(heading)
    print(
        "Separate names with commas."
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


def print_roster(
    session: LiveDraftSession,
) -> None:
    team = session.state.user_team

    print("\n" + "=" * 62)
    print(
        f" YOUR ROSTER — TEAM "
        f"{session.user_team_number}"
    )
    print("=" * 62)

    if not team.players:
        print(
            "No players drafted yet."
        )

    else:
        for player in team.players:
            print(
                f"{player.position:<5} | "
                f"{player.name:<25} | "
                f"Rank {player.rank}"
            )

    print("-" * 62)

    print(
        f"QB {team.count_position('QB')} | "
        f"RB {team.count_position('RB')} | "
        f"WR {team.count_position('WR')} | "
        f"TE {team.count_position('TE')} | "
        f"DST {team.count_position('DST')} | "
        f"K {team.count_position('K')}"
    )

    print(
        f"Players drafted: "
        f"{len(team.players)}/16"
    )


def enter_opponent_picks(
    session: LiveDraftSession,
) -> None:
    while (
        not session.is_complete
        and not session.is_user_turn
    ):
        overall_pick = session.current_pick
        team_number = session.current_team_number

        print(
            f"\nPick {overall_pick} — "
            f"Team {team_number}"
        )

        player_name = input(
            "Player drafted: "
        ).strip()

        if not player_name:
            print(
                "Please enter a player name."
            )
            continue

        try:
            draft_pick = session.record_pick(
                player_name
            )

        except ValueError as error:
            print(
                f"Error: {error}"
            )
            continue

        print(
            f"Recorded: "
            f"{draft_pick.player.name}"
        )


def validate_candidates(
    session: LiveDraftSession,
    player_names: tuple[str, ...],
) -> tuple[str, ...]:
    valid_players: list[str] = []
    seen_names: set[str] = set()

    for player_name in player_names:
        normalized_name = normalize_name(
            player_name
        )

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)

        player = session.player_for_name(
            player_name
        )

        if player is None:
            print(
                f"- Not recognized: "
                f"{player_name}"
            )

            suggestions = (
                session.name_suggestions(
                    player_name
                )
            )

            if suggestions:
                print(
                    "  Suggestions: "
                    + ", ".join(suggestions)
                )

            continue

        if not session.board.is_available(player):
            print(
                f"- Already drafted: "
                f"{player.name}"
            )
            continue

        valid_players.append(
            player.name
        )

    return tuple(valid_players)


def print_available_board(
    session: LiveDraftSession,
    limit: int = 15,
) -> None:
    print("\n" + "=" * 62)
    print(
        f" TOP {limit} AVAILABLE BY "
        f"FANTASYPROS RANK"
    )
    print("=" * 62)

    for player in session.available_players(
        limit=limit
    ):
        print(
            f"{player.rank:>3} | "
            f"{player.position:<4} | "
            f"{player.name}"
        )


def print_recommendations(
    recommendations,
    current_pick: int,
    next_pick: int,
    runtime: float,
) -> None:
    print("\n" + "=" * 116)
    print(
        " GRIDIRON AI — LIVE RECOMMENDATIONS"
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
        print(
            "No valid recommendations were produced."
        )
        return

    top = recommendations[0]

    print("\n" + "=" * 116)
    print(
        f" TOP PICK: "
        f"{top.player_name} "
        f"({top.position})"
    )
    print(
        f" Grade: {top.grade} | "
        f"Score: {top.score:.1f} | "
        f"Action: {top.action}"
    )
    print("=" * 116)

    for reason in top.reasons:
        print(
            f"- {reason}"
        )


def run_user_pick(
    session: LiveDraftSession,
    simulations: int,
    wait_analyzer: WaitAnalyzer,
    recommendation_engine: RecommendationEngine,
) -> None:
    current_pick = session.current_pick
    next_pick = session.next_user_pick

    print_roster(session)
    print_available_board(session)

    if next_pick is None:
        print(
            "\nThis is your final draft pick."
        )

        selected_player = input(
            "Player you drafted: "
        ).strip()

        session.record_pick(
            selected_player
        )

        return

    candidate_names = read_player_names(
        heading=(
            "Enter the available players "
            "you want Gridiron AI to compare."
        )
    )

    valid_candidates = validate_candidates(
        session=session,
        player_names=candidate_names,
    )

    if not valid_candidates:
        print(
            "\nNo valid available candidates "
            "were entered."
        )
        return

    print(
        f"\nRunning {simulations} live-state "
        f"counterfactual simulations..."
    )

    start_time = perf_counter()

    wait_results = (
        wait_analyzer.analyze_live_players(
            player_names=valid_candidates,
            draft_slot=(
                session.user_team_number
            ),
            completed_player_names=(
                session.completed_player_names
            ),
            current_pick=current_pick,
            next_pick=next_pick,
            simulations=simulations,
        )
    )

    recommendations = (
        recommendation_engine.recommend(
            wait_results=wait_results,
            user_team=session.state.user_team,
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

    while True:
        selected_player = input(
            "\nPlayer you actually drafted: "
        ).strip()

        try:
            draft_pick = session.record_pick(
                selected_player
            )

        except ValueError as error:
            print(
                f"Error: {error}"
            )
            continue

        print(
            f"Recorded your pick: "
            f"{draft_pick.player.name}"
        )
        break


def main() -> None:
    print("\n" + "=" * 58)
    print(
        "           GRIDIRON AI — "
        "LIVE DRAFT MODE"
    )
    print("=" * 58)

    draft_slot = read_integer(
        prompt="Your draft slot",
        minimum=1,
        maximum=10,
        default=7,
    )

    simulations = read_integer(
        prompt="Simulations per candidate",
        minimum=10,
        default=DEFAULT_SIMULATIONS,
    )

    session = LiveDraftSession(
        user_team_number=draft_slot
    )

    wait_analyzer = WaitAnalyzer()

    recommendation_engine = (
        RecommendationEngine(
            players=wait_analyzer.players,
            projections=load_projections(),
            approved_players=(
                wait_analyzer.approved_players
            ),
        )
    )

    while not session.is_complete:
        enter_opponent_picks(
            session
        )

        if session.is_complete:
            break

        if session.is_user_turn:
            run_user_pick(
                session=session,
                simulations=simulations,
                wait_analyzer=wait_analyzer,
                recommendation_engine=(
                    recommendation_engine
                ),
            )

    print("\n" + "=" * 58)
    print(" DRAFT COMPLETE")
    print("=" * 58)

    print_roster(session)


if __name__ == "__main__":
    main()