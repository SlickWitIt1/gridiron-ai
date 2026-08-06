from collections.abc import Iterable

from player import Player
from preferences import load_my_guys, normalize_name
from projection import Projection
from projection_loader import load_projections
from recommendation import Recommendation
from team import base_position
from wait_analyzer import WaitAnalysis


class RecommendationEngine:
    REPLACEMENT_INDEX = {
        "QB": 10,
        "RB": 30,
        "WR": 30,
        "TE": 10,
        "DST": 10,
        "K": 10,
    }

    def __init__(
        self,
        players: Iterable[Player],
        projections: dict[str, Projection] | None = None,
        approved_players: set[str] | None = None,
    ) -> None:
        self.players_by_name = {
            normalize_name(player.name): player
            for player in players
        }

        self.projections = (
            projections
            if projections is not None
            else load_projections()
        )

        self.approved_players = (
            approved_players
            if approved_players is not None
            else load_my_guys()
        )

        self.replacement_points = (
            self._calculate_replacement_points()
        )

    def _calculate_replacement_points(
        self,
    ) -> dict[str, float]:
        points_by_position: dict[
            str,
            list[float],
        ] = {}

        for projection in self.projections.values():
            points_by_position.setdefault(
                projection.position,
                [],
            ).append(
                projection.fantasy_points
            )

        replacement_points: dict[str, float] = {}

        for position, points in points_by_position.items():
            points.sort(reverse=True)

            replacement_number = (
                self.REPLACEMENT_INDEX.get(
                    position,
                    10,
                )
            )

            replacement_index = (
                replacement_number - 1
            )

            if not points:
                replacement_points[position] = 0.0

            elif replacement_index < len(points):
                replacement_points[position] = (
                    points[replacement_index]
                )

            else:
                replacement_points[position] = (
                    points[-1]
                )

        return replacement_points

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return "A+"

        if score >= 82:
            return "A"

        if score >= 74:
            return "B+"

        if score >= 66:
            return "B"

        if score >= 58:
            return "C+"

        if score >= 50:
            return "C"

        return "D"

    @staticmethod
    def _action(
        survival_probability: float | None,
    ) -> str:
        if survival_probability is None:
            return "UNLIKELY AVAILABLE"

        if survival_probability < 0.25:
            return "DRAFT NOW"

        if survival_probability < 0.60:
            return "RISKY TO WAIT"

        if survival_probability < 0.85:
            return "CAN PROBABLY WAIT"

        return "SAFE TO WAIT"

    def recommend(
        self,
        wait_results: Iterable[WaitAnalysis],
    ) -> list[Recommendation]:
        prepared_results: list[
            tuple[
                WaitAnalysis,
                Player,
                Projection,
                float,
                bool,
            ]
        ] = []

        for wait_result in wait_results:
            normalized_name = normalize_name(
                wait_result.player_name
            )

            player = self.players_by_name.get(
                normalized_name
            )

            projection = self.projections.get(
                normalized_name
            )

            if player is None or projection is None:
                continue

            position = base_position(
                player.position
            )

            replacement_points = (
                self.replacement_points.get(
                    position,
                    0.0,
                )
            )

            projection_advantage = (
                projection.fantasy_points
                - replacement_points
            )

            is_my_guy = (
                normalized_name
                in self.approved_players
            )

            prepared_results.append(
                (
                    wait_result,
                    player,
                    projection,
                    projection_advantage,
                    is_my_guy,
                )
            )

        if not prepared_results:
            return []

        advantages = [
            item[3]
            for item in prepared_results
        ]

        lowest_advantage = min(advantages)
        highest_advantage = max(advantages)

        advantage_spread = (
            highest_advantage
            - lowest_advantage
        )

        recommendations: list[
            Recommendation
        ] = []

        for (
            wait_result,
            player,
            projection,
            projection_advantage,
            is_my_guy,
        ) in prepared_results:
            if advantage_spread == 0:
                value_score = 35.0

            else:
                value_score = 20.0 + (
                    (
                        projection_advantage
                        - lowest_advantage
                    )
                    / advantage_spread
                ) * 30.0

            survival_probability = (
                wait_result.survival_probability
            )

            urgency_score = (
                15.0
                if survival_probability is None
                else (
                    1.0
                    - survival_probability
                ) * 30.0
            )

            preference_score = (
                15.0
                if is_my_guy
                else 0.0
            )

            availability_score = (
                wait_result
                .available_now_probability
                * 5.0
            )

            score = min(
                100.0,
                value_score
                + urgency_score
                + preference_score
                + availability_score,
            )

            reasons: list[str] = [
                (
                    f"Projects for "
                    f"{projection.fantasy_points:.1f} "
                    f"points "
                    f"({projection_advantage:+.1f} "
                    f"versus the {position} "
                    f"replacement baseline)."
                )
            ]

            if is_my_guy:
                reasons.append(
                    "Marked as one of your My Guys."
                )

            if survival_probability is None:
                reasons.append(
                    "The model usually has him "
                    "gone before this pick."
                )

            elif survival_probability < 0.25:
                reasons.append(
                    f"Only a "
                    f"{survival_probability:.1%} "
                    f"chance to reach your next pick."
                )

            else:
                reasons.append(
                    f"A "
                    f"{survival_probability:.1%} "
                    f"chance to reach your next pick."
                )

            recommendations.append(
                Recommendation(
                    player_name=player.name,
                    position=position,
                    projected_points=(
                        projection.fantasy_points
                    ),
                    projection_advantage=(
                        projection_advantage
                    ),
                    is_my_guy=is_my_guy,
                    available_now_probability=(
                        wait_result
                        .available_now_probability
                    ),
                    survival_probability=(
                        survival_probability
                    ),
                    score=score,
                    grade=self._grade(score),
                    action=self._action(
                        survival_probability
                    ),
                    reasons=tuple(reasons),
                )
            )

        return sorted(
            recommendations,
            key=lambda recommendation: (
                recommendation.score
            ),
            reverse=True,
        )