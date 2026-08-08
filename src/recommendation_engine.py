from collections.abc import Iterable

from player import Player
from preferences import load_my_guys, normalize_name
from projection import Projection
from projection_loader import load_projections
from recommendation import Recommendation
from recommendation_score import RecommendationScore
from strategy import DraftStrategy, StrategyResult
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

    PROJECTION_MAX = 24.0
    WAIT_RISK_MAX = 13.0
    ROSTER_FIT_MAX = 14.0
    SCARCITY_MAX = 7.0
    TIER_DROP_MAX = 8.0
    OPPORTUNITY_COST_MAX = 8.0
    STRATEGY_FIT_MAX = 9.0
    RUN_PRESSURE_MAX = 12.0
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


    @classmethod
    def strategy_fit(
        cls,
        strategy_result: StrategyResult | None,
        team: Team,
        position: str,
        tier_info: TierInfo,
    ) -> tuple[float, str, str]:
        """Score how naturally a candidate continues the detected build.

        Strategy is intentionally a modifier, not a hard rule. Even a poor
        structural fit can still win through projection, tier, and wait value.
        """
        if (
            strategy_result is None
            or strategy_result.primary_strategy == DraftStrategy.UNDETERMINED
        ):
            return (
                cls.STRATEGY_FIT_MAX * 0.5,
                "NEUTRAL",
                "The draft strategy is still developing, so best value remains the priority.",
            )

        strategy = strategy_result.primary_strategy
        score = cls.STRATEGY_FIT_MAX * 0.5
        label = "NEUTRAL"
        explanation = f"Neutral fit for the emerging {strategy.value} build."

        preferred: set[str] = set()
        acceptable: set[str] = set()
        discouraged: set[str] = set()

        if strategy == DraftStrategy.HERO_RB:
            preferred = {"WR"}
            acceptable = {"TE", "QB"}
            discouraged = {"RB"}
        elif strategy == DraftStrategy.ZERO_RB:
            early_zero_rb = any(
                "RB only" in priority
                for priority in strategy_result.next_priorities
            )
            preferred = {"WR", "TE"} if early_zero_rb else {"RB"}
            acceptable = {"QB", "WR", "TE"}
            discouraged = {"RB"} if early_zero_rb else set()
        elif strategy == DraftStrategy.ROBUST_RB:
            preferred = {"WR"}
            acceptable = {"TE", "QB"}
            discouraged = {"RB"}
        elif strategy == DraftStrategy.WR_HEAVY:
            preferred = {"RB"}
            acceptable = {"QB", "TE"}
            discouraged = {"WR"}
        elif strategy == DraftStrategy.ELITE_QB:
            preferred = {"RB", "WR"}
            acceptable = {"TE"}
            discouraged = {"QB"}
        elif strategy == DraftStrategy.ELITE_TE:
            preferred = {"RB", "WR"}
            acceptable = {"QB"}
            discouraged = {"TE"}
        elif strategy == DraftStrategy.BALANCED:
            if team.needs_position(position):
                preferred = {position}
            acceptable = {"RB", "WR", "QB", "TE"}

        if position in preferred:
            score = cls.STRATEGY_FIT_MAX
            label = "EXCELLENT"
            explanation = (
                f"Excellent continuation of your {strategy.value} build; "
                f"{position} is a preferred next step."
            )
        elif position in acceptable:
            score = cls.STRATEGY_FIT_MAX * 0.72
            label = "GOOD"
            explanation = (
                f"Good structural fit for your {strategy.value} build without "
                "forcing the strategy over player value."
            )
        elif position in discouraged:
            # A critical tier cliff can justify temporarily breaking structure.
            if tier_info.urgency in {"CRITICAL", "HIGH"}:
                score = cls.STRATEGY_FIT_MAX * 0.45
                label = "VALUE EXCEPTION"
                explanation = (
                    f"Another {position} is not the cleanest {strategy.value} "
                    "continuation, but the tier pressure may justify it."
                )
            else:
                score = cls.STRATEGY_FIT_MAX * 0.15
                label = "POOR"
                explanation = (
                    f"This pick weakens the current {strategy.value} structure; "
                    "consider the listed priorities unless the value is exceptional."
                )

        return score, label, explanation

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

    def _run_pressure(self, *, forecast, position: str) -> tuple[float, float, float]:
        if forecast is None:
            return 0.0, 0.0, 0.0
        position_forecast = forecast.position(position)
        if position_forecast is None:
            return 0.0, 0.0, 0.0

        expected = float(position_forecast.expected_picks)
        run_probability = float(position_forecast.run_probability)
        picks_between = max(1, int(forecast.picks_between))
        volume_share = self._clamp(expected / picks_between, 0.0, 1.0)
        pressure = self.RUN_PRESSURE_MAX * (
            run_probability * 0.65 + volume_share * 0.35
        )
        return (
            self._clamp(pressure, 0.0, self.RUN_PRESSURE_MAX),
            expected,
            run_probability,
        )

    def recommend(
        self,
        wait_results: Iterable[WaitAnalysis],
        user_team: Team,
        available_player_names: Iterable[str] | None = None,
        strategy_result: StrategyResult | None = None,
        forecast=None,
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
            strategy_fit_score, strategy_fit_label, strategy_fit_explanation = (
                self.strategy_fit(
                    strategy_result=strategy_result,
                    team=user_team,
                    position=position,
                    tier_info=tier_info,
                )
            )
            run_pressure_component, expected_position_picks, position_run_probability = (
                self._run_pressure(forecast=forecast, position=position)
            )

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
                    "strategy_fit_score": strategy_fit_score,
                    "strategy_fit_label": strategy_fit_label,
                    "strategy_fit_explanation": strategy_fit_explanation,
                    "run_pressure_component": run_pressure_component,
                    "expected_position_picks": expected_position_picks,
                    "position_run_probability": position_run_probability,
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
            strategy_fit_score = float(item["strategy_fit_score"])
            strategy_fit_label = str(item["strategy_fit_label"])
            strategy_fit_explanation = str(item["strategy_fit_explanation"])
            run_pressure_component = float(item["run_pressure_component"])
            expected_position_picks = float(item["expected_position_picks"])
            position_run_probability = float(item["position_run_probability"])

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

            opportunity_cost = wait_result.opportunity_cost
            opportunity_cost_component = self._normalize(
                max(0.0, opportunity_cost),
                0.0,
                25.0,
                self.OPPORTUNITY_COST_MAX,
            )

            strategy_fit_component = self._clamp(
                strategy_fit_score,
                0.0,
                self.STRATEGY_FIT_MAX,
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
                opportunity_cost_component,
                strategy_fit_component,
                run_pressure_component,
                preference_component,
            )

            total_score = self._clamp(
                sum(component_values),
                0.0,
                100.0,
            )

            # Roster-path opportunity cost comes directly from paired
            # counterfactual simulations. Positive means taking this player
            # now produced more projected value across the current and next
            # user selections; negative means the pass path performed better.
            expected_value_lost = max(0.0, opportunity_cost)
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
            reasons.append(strategy_fit_explanation)

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

            if opportunity_cost >= 3.0:
                pass_path = " then ".join(
                    name
                    for name in (
                        wait_result.likely_pass_current_player,
                        wait_result.likely_pass_next_player,
                    )
                    if name
                )
                take_next = wait_result.likely_take_next_player
                reasons.append(
                    f"The take-now path projects {opportunity_cost:.1f} "
                    f"points better across your next two picks."
                )
                if take_next and pass_path:
                    reasons.append(
                        f"Most likely paths: take {player.name} then "
                        f"{take_next}; passing most often leads to {pass_path}."
                    )
            elif opportunity_cost <= -3.0:
                reasons.append(
                    f"The simulated pass path projects "
                    f"{abs(opportunity_cost):.1f} points better across "
                    f"your next two picks."
                )

            if wait_result.tier_disappearance_probability >= 0.50:
                reasons.append(
                    f"There is a "
                    f"{wait_result.tier_disappearance_probability:.0%} "
                    f"chance this entire tier is gone by your next pick."
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

            if expected_position_picks >= 2.5 or position_run_probability >= 0.45:
                reasons.append(
                    f"Simulator expects {expected_position_picks:.1f} {position} "
                    f"picks before your next turn "
                    f"({position_run_probability:.0%} run probability)."
                )

            score_breakdown = RecommendationScore(
                total=total_score,
                projection=projection_component,
                wait_risk=wait_risk_component,
                roster_fit=roster_fit_component,
                scarcity=scarcity_component,
                tier_drop=tier_drop_component,
                opportunity_cost=opportunity_cost_component,
                strategy_fit=strategy_fit_component,
                run_pressure=run_pressure_component,
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
                    likely_take_next_player=(
                        wait_result.likely_take_next_player
                    ),
                    likely_pass_current_player=(
                        wait_result.likely_pass_current_player
                    ),
                    likely_pass_next_player=(
                        wait_result.likely_pass_next_player
                    ),
                    take_path_projected_points=(
                        wait_result.take_path_projected_points
                    ),
                    pass_path_projected_points=(
                        wait_result.pass_path_projected_points
                    ),
                    opportunity_cost=opportunity_cost,
                    tier_disappearance_probability=(
                        wait_result.tier_disappearance_probability
                    ),
                    primary_strategy=(
                        strategy_result.primary_strategy.value
                        if strategy_result is not None
                        else DraftStrategy.UNDETERMINED.value
                    ),
                    secondary_strategy=(
                        strategy_result.secondary_strategy.value
                        if (
                            strategy_result is not None
                            and strategy_result.secondary_strategy is not None
                        )
                        else None
                    ),
                    strategy_confidence=(
                        strategy_result.confidence
                        if strategy_result is not None
                        else 0
                    ),
                    strategy_priorities=(
                        strategy_result.next_priorities
                        if strategy_result is not None
                        else ("Best Value",)
                    ),
                    strategy_fit_score=strategy_fit_component,
                    strategy_fit_label=strategy_fit_label,
                    strategy_fit_explanation=strategy_fit_explanation,
                    expected_position_picks=expected_position_picks,
                    position_run_probability=position_run_probability,
                    run_pressure_score=run_pressure_component,
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
