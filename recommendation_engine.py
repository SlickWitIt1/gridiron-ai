from collections.abc import Iterable

from player import Player
from preferences import load_my_guys, normalize_name
from projection import Projection
from projection_loader import load_projections
from recommendation import Recommendation
from team import Team, base_position
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

    STARTER_NEED_BONUS = 18.0
    FLEX_NEED_BONUS = 8.0

    BACKUP_QB_PENALTY = 12.0
    THIRD_QB_PENALTY = 30.0

    BACKUP_TE_PENALTY = 7.0
    THIRD_TE_PENALTY = 20.0

    EXTRA_DST_PENALTY = 40.0
    EXTRA_K_PENALTY = 40.0

    RB_DEPTH_BONUS = 5.0
    WR_DEPTH_BONUS = 5.0

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

    def roster_fit(
        self,
        team: Team,
        position: str,
    ) -> tuple[float, tuple[str, ...]]:
        score = 0.0
        reasons: list[str] = []

        position_count = team.count_position(
            position
        )

        if team.needs_position(position):
            score += self.STARTER_NEED_BONUS

            reasons.append(
                f"Fills an open {position} "
                f"starting or FLEX need."
            )

        if (
            position in {"RB", "WR", "TE"}
            and team.flex_slots_filled() == 0
            and not team.needs_position(position)
        ):
            score += self.FLEX_NEED_BONUS

            reasons.append(
                "Can help fill the open FLEX slot."
            )

        if position == "RB":
            if position_count < 4:
                score += self.RB_DEPTH_BONUS

                reasons.append(
                    "Adds valuable running-back depth."
                )

        elif position == "WR":
            if position_count < 4:
                score += self.WR_DEPTH_BONUS

                reasons.append(
                    "Adds valuable wide-receiver depth."
                )

        elif position == "QB":
            if position_count == 1:
                score -= self.BACKUP_QB_PENALTY

                reasons.append(
                    "You already have a starting QB."
                )

            elif position_count >= 2:
                score -= self.THIRD_QB_PENALTY

                reasons.append(
                    "A third QB would use a valuable "
                    "bench spot."
                )

        elif position == "TE":
            if position_count == 1:
                score -= self.BACKUP_TE_PENALTY

                reasons.append(
                    "You already have a starting TE."
                )

            elif position_count >= 2:
                score -= self.THIRD_TE_PENALTY

                reasons.append(
                    "A third TE would use a valuable "
                    "bench spot."
                )

        elif position == "DST":
            if position_count >= 1:
                score -= self.EXTRA_DST_PENALTY

                reasons.append(
                    "You already have a defense."
                )

        elif position == "K":
            if position_count >= 1:
                score -= self.EXTRA_K_PENALTY

                reasons.append(
                    "You already have a kicker."
                )

        if not team.can_draft(position):
            score = -100.0

            reasons.append(
                f"Your roster cannot legally add "
                f"another {position}."
            )

        return score, tuple(reasons)

    def recommend(
        self,
        wait_results: Iterable[WaitAnalysis],
        user_team: Team,
    ) -> list[Recommendation]:
        prepared_results: list[
            tuple[
                WaitAnalysis,
                Player,
                Projection,
                float,
                bool,
                float,
                tuple[str, ...],
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

            if not user_team.can_draft(position):
                continue

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

            (
                roster_fit_score,
                roster_reasons,
            ) = self.roster_fit(
                team=user_team,
                position=position,
            )

            prepared_results.append(
                (
                    wait_result,
                    player,
                    projection,
                    projection_advantage,
                    is_my_guy,
                    roster_fit_score,
                    roster_reasons,
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
            roster_fit_score,
            roster_reasons,
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

            score = max(
                0.0,
                min(
                    100.0,
                    value_score
                    + urgency_score
                    + preference_score
                    + availability_score
                    + roster_fit_score,
                ),
            )

            position = base_position(
                player.position
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

            reasons.extend(
                roster_reasons
            )

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
                    roster_fit_score=(
                        roster_fit_score
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