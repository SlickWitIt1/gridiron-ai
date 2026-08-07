from collections.abc import Iterable

from player import Player
from preferences import load_my_guys, normalize_name
from projection import Projection
from projection_loader import load_projections
from recommendation import Recommendation
from recommendation_score import RecommendationScore
from team import Team, base_position
from tier import TierInfo
from tier_engine import TierEngine
from wait_analyzer import WaitAnalysis


class RecommendationEngine:
    """Create explainable, roster-aware draft recommendations."""

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

    PROJECTION_MAX = 35.0
    WAIT_RISK_MAX = 20.0
    ROSTER_FIT_MAX = 15.0
    SCARCITY_MAX = 10.0
    TIER_DROP_MAX = 15.0
    PREFERENCE_MAX = 5.0

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

        self.replacement_points = self._calculate_replacement_points()
        self.tier_engine = TierEngine(self.projections)

    def _calculate_replacement_points(self) -> dict[str, float]:
        points_by_position: dict[str, list[float]] = {}

        for projection in self.projections.values():
            points_by_position.setdefault(
                projection.position,
                [],
            ).append(projection.fantasy_points)

        replacement_points: dict[str, float] = {}

        for position, points in points_by_position.items():
            points.sort(reverse=True)
            replacement_number = self.REPLACEMENT_INDEX.get(position, 10)
            replacement_index = replacement_number - 1

            if not points:
                replacement_points[position] = 0.0
            elif replacement_index < len(points):
                replacement_points[position] = points[replacement_index]
            else:
                replacement_points[position] = points[-1]

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
    def _action(survival_probability: float | None) -> str:
        if survival_probability is None:
            return "UNLIKELY AVAILABLE"
        if survival_probability < 0.25:
            return "DRAFT NOW"
        if survival_probability < 0.60:
            return "RISKY TO WAIT"
        if survival_probability < 0.85:
            return "CAN PROBABLY WAIT"
        return "SAFE TO WAIT"

    @staticmethod
    def _roster_need_label(roster_fit_score: float) -> str:
        if roster_fit_score >= 18:
            return "HIGH NEED"
        if roster_fit_score >= 8:
            return "GOOD FIT"
        if roster_fit_score >= 0:
            return "NEUTRAL"
        return "LOW NEED"

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return min(maximum, max(minimum, value))

    @classmethod
    def _normalize(
        cls,
        value: float,
        minimum: float,
        maximum: float,
        output_maximum: float,
    ) -> float:
        if maximum <= minimum:
            return output_maximum * 0.5

        ratio = (value - minimum) / (maximum - minimum)
        return cls._clamp(ratio, 0.0, 1.0) * output_maximum

    @classmethod
    def _confidence(
        cls,
        total_score: float,
        survival_probability: float | None,
        tier_drop_points: float,
        component_values: tuple[float, ...],
    ) -> int:
        score_strength = cls._clamp(total_score, 0.0, 100.0)

        wait_certainty = (
            72.0
            if survival_probability is None
            else abs(0.5 - survival_probability) * 200.0
        )

        tier_certainty = cls._clamp(
            tier_drop_points / 20.0 * 100.0,
            0.0,
            100.0,
        )

        strongest_component = max(component_values, default=0.0)
        component_clarity = cls._clamp(
            strongest_component / 35.0 * 100.0,
            0.0,
            100.0,
        )

        confidence = (
            score_strength * 0.50
            + wait_certainty * 0.25
            + tier_certainty * 0.15
            + component_clarity * 0.10
        )

        return round(cls._clamp(confidence, 0.0, 100.0))

    def roster_fit(
        self,
        team: Team,
        position: str,
    ) -> tuple[float, tuple[str, ...]]:
        score = 0.0
        reasons: list[str] = []
        position_count = team.count_position(position)

        if team.needs_position(position):
            score += self.STARTER_NEED_BONUS
            reasons.append(
                f"Fills an open {position} starting or FLEX need."
            )

        if (
            position in {"RB", "WR", "TE"}
            and team.flex_slots_filled() == 0
            and not team.needs_position(position)
        ):
            score += self.FLEX_NEED_BONUS
            reasons.append("Can help fill the open FLEX slot.")

        if position == "RB":
            if position_count < 4:
                score += self.RB_DEPTH_BONUS
                reasons.append("Adds valuable running-back depth.")

        elif position == "WR":
            if position_count < 4:
                score += self.WR_DEPTH_BONUS
                reasons.append("Adds valuable wide-receiver depth.")

        elif position == "QB":
            if position_count == 1:
                score -= self.BACKUP_QB_PENALTY
                reasons.append("You already have a starting QB.")
            elif position_count >= 2:
                score -= self.THIRD_QB_PENALTY
                reasons.append(
                    "A third QB would use a valuable bench spot."
                )

        elif position == "TE":
            if position_count == 1:
                score -= self.BACKUP_TE_PENALTY
                reasons.append("You already have a starting TE.")
            elif position_count >= 2:
                score -= self.THIRD_TE_PENALTY
                reasons.append(
                    "A third TE would use a valuable bench spot."
                )

        elif position == "DST":
            if position_count >= 1:
                score -= self.EXTRA_DST_PENALTY
                reasons.append("You already have a defense.")

        elif position == "K":
            if position_count >= 1:
                score -= self.EXTRA_K_PENALTY
                reasons.append("You already have a kicker.")

        if not team.can_draft(position):
            score = -100.0
            reasons.append(
                f"Your roster cannot legally add another {position}."
            )

        return score, tuple(reasons)

    @staticmethod
    def _fallback_tier_info(
        player_name: str,
        position: str,
        projected_points: float,
    ) -> TierInfo:
        return TierInfo(
            player_name=player_name,
            position=position,
            tier_number=0,
            tier_size=1,
            players_remaining=1,
            projected_points=projected_points,
            drop_to_next_tier=0.0,
            urgency="LOW",
            is_last_in_tier=True,
        )

    def recommend(
        self,
        wait_results: Iterable[WaitAnalysis],
        user_team: Team,
        available_player_names: Iterable[str] | None = None,
    ) -> list[Recommendation]:
        available_names = (
            set(available_player_names)
            if available_player_names is not None
            else None
        )

        tier_info_by_name = self.tier_engine.build_tiers(
            available_names=available_names
        )

        prepared_results: list[dict[str, object]] = []

        for wait_result in wait_results:
            normalized_name = normalize_name(wait_result.player_name)
            player = self.players_by_name.get(normalized_name)
            projection = self.projections.get(normalized_name)

            if player is None or projection is None:
                continue

            position = base_position(player.position)

            if not user_team.can_draft(position):
                continue

            replacement_points = self.replacement_points.get(position, 0.0)
            projection_advantage = (
                projection.fantasy_points - replacement_points
            )
            is_my_guy = normalized_name in self.approved_players
            roster_fit_score, roster_reasons = self.roster_fit(
                team=user_team,
                position=position,
            )
            tier_info = tier_info_by_name.get(
                normalized_name,
                self._fallback_tier_info(
                    player_name=player.name,
                    position=position,
                    projected_points=projection.fantasy_points,
                ),
            )
            tier_drop_points = tier_info.drop_to_next_tier

            prepared_results.append(
                {
                    "wait_result": wait_result,
                    "player": player,
                    "projection": projection,
                    "position": position,
                    "projection_advantage": projection_advantage,
                    "is_my_guy": is_my_guy,
                    "roster_fit_score": roster_fit_score,
                    "roster_reasons": roster_reasons,
                    "tier_info": tier_info,
                    "tier_drop_points": tier_drop_points,
                }
            )

        if not prepared_results:
            return []

        recommendations: list[Recommendation] = []

        for item in prepared_results:
            wait_result = item["wait_result"]
            player = item["player"]
            projection = item["projection"]
            position = str(item["position"])
            projection_advantage = float(item["projection_advantage"])
            is_my_guy = bool(item["is_my_guy"])
            roster_fit_score = float(item["roster_fit_score"])
            roster_reasons = item["roster_reasons"]
            tier_info = item["tier_info"]
            tier_drop_points = float(item["tier_drop_points"])

            # Score projection value against a stable replacement-level
            # scale. This avoids a player's score changing simply because
            # the user selected a different comparison group.
            projection_component = self._normalize(
                max(0.0, projection_advantage),
                0.0,
                80.0,
                self.PROJECTION_MAX,
            )

            survival_probability = wait_result.survival_probability
            wait_risk = (
                1.0
                if survival_probability is None
                else 1.0 - survival_probability
            )
            wait_risk_component = (
                self._clamp(wait_risk, 0.0, 1.0)
                * self.WAIT_RISK_MAX
            )

            roster_fit_component = self._normalize(
                roster_fit_score,
                -40.0,
                23.0,
                self.ROSTER_FIT_MAX,
            )

            # Scarcity reflects how sharply the position falls after this
            # player, while tier_drop_component rewards especially large
            # cliffs. Keeping this separate from raw projection prevents
            # double-counting the same signal.
            tier_pressure = {
                "CRITICAL": 1.0,
                "HIGH": 0.80,
                "MEDIUM": 0.55,
                "LOW": 0.25,
            }.get(tier_info.urgency, 0.25)
            scarcity_component = self._clamp(
                (
                    self._normalize(
                        tier_drop_points,
                        0.0,
                        12.0,
                        self.SCARCITY_MAX,
                    )
                    * 0.65
                    + tier_pressure * self.SCARCITY_MAX * 0.35
                ),
                0.0,
                self.SCARCITY_MAX,
            )

            tier_drop_component = self._normalize(
                tier_drop_points,
                0.0,
                25.0,
                self.TIER_DROP_MAX,
            )

            preference_component = (
                self.PREFERENCE_MAX if is_my_guy else 0.0
            )

            component_values = (
                projection_component,
                wait_risk_component,
                roster_fit_component,
                scarcity_component,
                tier_drop_component,
                preference_component,
            )

            total_score = self._clamp(
                sum(component_values),
                0.0,
                100.0,
            )

            expected_value_lost = tier_drop_points * wait_risk
            confidence = self._confidence(
                total_score=total_score,
                survival_probability=survival_probability,
                tier_drop_points=tier_drop_points,
                component_values=component_values,
            )

            roster_need = self._roster_need_label(roster_fit_score)

            reasons: list[str] = [
                (
                    f"{projection.fantasy_points:.1f} projected points "
                    f"({projection_advantage:+.1f} above the {position} "
                    f"replacement baseline)."
                ),
            ]
            reasons.extend(roster_reasons)

            if tier_info.tier_number > 0:
                tier_label = f"{position} Tier {tier_info.tier_number}"
                if tier_info.is_last_in_tier:
                    reasons.append(
                        f"Last available player in {tier_label}."
                    )
                else:
                    reasons.append(
                        f"{tier_label}: {tier_info.players_remaining} "
                        f"players remain in this tier."
                    )

            if tier_drop_points >= 10.0:
                reasons.append(
                    f"The next tier begins {tier_drop_points:.1f} "
                    f"projected points lower."
                )
            elif tier_drop_points > 0.0:
                reasons.append(
                    f"The next tier is {tier_drop_points:.1f} "
                    f"projected points lower."
                )

            if expected_value_lost >= 3.0:
                reasons.append(
                    f"Waiting risks about {expected_value_lost:.1f} "
                    f"projected points of value."
                )

            if is_my_guy:
                reasons.append(
                    "This player is on your My Guys list."
                )

            if survival_probability is None:
                reasons.append(
                    "The model usually has him gone before this pick."
                )
            elif survival_probability < 0.25:
                reasons.append(
                    f"Only a {survival_probability:.1%} chance to "
                    f"reach your next pick."
                )
            else:
                reasons.append(
                    f"A {survival_probability:.1%} chance to reach "
                    f"your next pick."
                )

            score_breakdown = RecommendationScore(
                total=total_score,
                projection=projection_component,
                wait_risk=wait_risk_component,
                roster_fit=roster_fit_component,
                scarcity=scarcity_component,
                tier_drop=tier_drop_component,
                preference=preference_component,
                confidence=confidence,
            )

            recommendations.append(
                Recommendation(
                    player_name=player.name,
                    position=position,
                    projected_points=projection.fantasy_points,
                    projection_advantage=projection_advantage,
                    is_my_guy=is_my_guy,
                    available_now_probability=(
                        wait_result.available_now_probability
                    ),
                    survival_probability=survival_probability,
                    roster_fit_score=roster_fit_score,
                    roster_need=roster_need,
                    tier_number=tier_info.tier_number,
                    tier_size=tier_info.tier_size,
                    players_remaining_in_tier=(
                        tier_info.players_remaining
                    ),
                    tier_drop_points=tier_drop_points,
                    tier_urgency=tier_info.urgency,
                    is_last_in_tier=tier_info.is_last_in_tier,
                    expected_value_lost=expected_value_lost,
                    score_breakdown=score_breakdown,
                    grade=self._grade(total_score),
                    action=self._action(survival_probability),
                    reasons=tuple(reasons),
                )
            )

        return sorted(
            recommendations,
            key=lambda recommendation: recommendation.score,
            reverse=True,
        )
