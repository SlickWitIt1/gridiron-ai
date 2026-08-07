from __future__ import annotations

from typing import Any, Iterable

from coach import CoachMessage, CoachMessageType, CoachSeverity


class CoachEngine:
    """Translate draft intelligence into concise, deterministic coaching copy.

    The engine intentionally accepts recommendation, strategy, and forecast
    objects by interface rather than concrete class. That keeps the coach
    independent from the recommendation and simulation engines and makes it
    reusable by the UI, save system, and future timeline features.
    """

    MAX_BULLETS = 4

    @staticmethod
    def _normalize(value: str | None) -> str:
        return (value or "").casefold().strip()

    @staticmethod
    def _strategy_name(strategy_result: Any | None) -> str | None:
        if strategy_result is None:
            return None
        strategy = getattr(strategy_result, "primary_strategy", None)
        if strategy is None:
            strategy = getattr(strategy_result, "strategy", None)
        if strategy is None:
            return None
        return str(getattr(strategy, "value", strategy))

    @staticmethod
    def _player_forecast(forecast: Any | None, player_name: str) -> Any | None:
        if forecast is None:
            return None
        lookup = getattr(forecast, "player", None)
        if callable(lookup):
            return lookup(player_name)
        target = CoachEngine._normalize(player_name)
        for item in getattr(forecast, "player_forecasts", ()):
            if CoachEngine._normalize(getattr(item, "player_name", None)) == target:
                return item
        return None

    @staticmethod
    def _tier_forecast(
        forecast: Any | None,
        position: str,
        tier_number: int,
    ) -> Any | None:
        if forecast is None or tier_number <= 0:
            return None
        for item in getattr(forecast, "tier_forecasts", ()):
            if (
                str(getattr(item, "position", "")).upper() == position.upper()
                and int(getattr(item, "tier_number", 0)) == tier_number
            ):
                return item
        return None

    @classmethod
    def recommendation_message(
        cls,
        recommendations: Iterable[Any],
        forecast: Any | None = None,
        strategy_result: Any | None = None,
    ) -> CoachMessage:
        ranked = tuple(recommendations)
        if not ranked:
            return CoachMessage(
                message_type=CoachMessageType.UPDATE,
                severity=CoachSeverity.INFO,
                title="AI COACH",
                summary="No recommendation is available yet.",
                bullets=("Select candidates and run an analysis.",),
                action="Keep taking value while the board develops.",
            )

        recommendation = ranked[0]
        player_name = str(getattr(recommendation, "player_name", "Top candidate"))
        bullets: list[str] = []

        if bool(getattr(recommendation, "is_last_in_tier", False)):
            tier_number = int(getattr(recommendation, "tier_number", 0))
            position = str(getattr(recommendation, "position", ""))
            label = f"{position} Tier {tier_number}" if tier_number > 0 else position
            bullets.append(f"Last available player in {label}.")
        else:
            remaining = int(getattr(recommendation, "players_remaining_in_tier", 0))
            tier_number = int(getattr(recommendation, "tier_number", 0))
            if tier_number > 0 and remaining > 0:
                bullets.append(
                    f"{remaining} players remain in Tier {tier_number} at this position."
                )

        survival = getattr(recommendation, "survival_probability", None)
        player_forecast = cls._player_forecast(forecast, player_name)
        if player_forecast is not None:
            survival = getattr(player_forecast, "survival_probability", survival)
        if survival is not None:
            survival = float(survival)
            if survival < 0.25:
                bullets.append(f"Only a {survival:.0%} chance to reach your next pick.")
            elif survival < 0.60:
                bullets.append(f"Waiting is risky: {survival:.0%} projected survival.")

        strategy_label = str(getattr(recommendation, "strategy_fit_label", "")).upper()
        strategy_name = (
            str(getattr(recommendation, "primary_strategy", ""))
            or cls._strategy_name(strategy_result)
        )
        if strategy_label in {"EXCELLENT", "GOOD"} and strategy_name:
            bullets.append(f"{strategy_label.title()} fit for your {strategy_name} build.")
        elif strategy_label in {"POOR", "VALUE EXCEPTION"}:
            explanation = str(
                getattr(recommendation, "strategy_fit_explanation", "")
            ).strip()
            if explanation:
                bullets.append(explanation)

        opportunity_cost = float(getattr(recommendation, "opportunity_cost", 0.0))
        if opportunity_cost >= 3.0:
            bullets.append(
                f"The take-now path leads by {opportunity_cost:.1f} projected points."
            )
        elif opportunity_cost <= -3.0:
            bullets.append(
                f"The simulated pass path leads by {abs(opportunity_cost):.1f} points."
            )

        run_position = getattr(forecast, "most_likely_run", None)
        run_probability = float(getattr(forecast, "run_probability", 0.0) or 0.0)
        if run_position and run_probability >= 0.55:
            bullets.append(
                f"A {run_position} run is projected at {run_probability:.0%}."
            )

        if not bullets:
            reasons = tuple(getattr(recommendation, "reasons", ()))
            bullets.extend(str(reason) for reason in reasons[:2])

        return CoachMessage(
            message_type=CoachMessageType.RECOMMENDATION,
            severity=CoachSeverity.POSITIVE,
            title="AI COACH",
            summary=f"Draft {player_name}.",
            bullets=tuple(bullets[: cls.MAX_BULLETS]),
            action=str(getattr(recommendation, "action", "")) or None,
            recommended_player=player_name,
        )

    @classmethod
    def selection_message(
        cls,
        selected_player_name: str,
        previous_recommendation: Any | None,
        previous_strategy: Any | None = None,
        current_strategy: Any | None = None,
        previous_forecast: Any | None = None,
        current_forecast: Any | None = None,
    ) -> CoachMessage:
        selected = selected_player_name.strip()
        recommended = (
            str(getattr(previous_recommendation, "player_name", "")).strip()
            if previous_recommendation is not None
            else ""
        )

        if recommended and cls._normalize(selected) == cls._normalize(recommended):
            bullets = ["You followed the top recommendation."]
            current_build = cls._strategy_name(current_strategy)
            if current_build and current_build != "Undetermined":
                bullets.append(f"Current build: {current_build}.")
            return CoachMessage(
                message_type=CoachMessageType.FOLLOWED,
                severity=CoachSeverity.POSITIVE,
                title="PICK REVIEW",
                summary=f"You selected {selected} as recommended.",
                bullets=tuple(bullets),
                action="Forecast and recommendations will update for the next decision.",
                recommended_player=recommended,
                selected_player=selected,
            )

        bullets: list[str] = []
        previous_build = cls._strategy_name(previous_strategy)
        current_build = cls._strategy_name(current_strategy)
        if (
            previous_build
            and current_build
            and previous_build != current_build
            and current_build != "Undetermined"
        ):
            bullets.append(f"Your build shifted from {previous_build} toward {current_build}.")

        if previous_recommendation is not None:
            position = str(getattr(previous_recommendation, "position", ""))
            tier_number = int(getattr(previous_recommendation, "tier_number", 0))
            tier = cls._tier_forecast(previous_forecast, position, tier_number)
            disappearance = (
                float(getattr(tier, "disappearance_probability", 0.0))
                if tier is not None
                else float(
                    getattr(
                        previous_recommendation,
                        "tier_disappearance_probability",
                        0.0,
                    )
                )
            )
            if disappearance >= 0.50 and position:
                tier_text = f" Tier {tier_number}" if tier_number > 0 else ""
                bullets.append(
                    f"There was a {disappearance:.0%} chance the {position}{tier_text} group would disappear."
                )

        if current_forecast is not None:
            run_position = getattr(current_forecast, "most_likely_run", None)
            run_probability = float(
                getattr(current_forecast, "run_probability", 0.0) or 0.0
            )
            if run_position and run_probability >= 0.55:
                bullets.append(
                    f"Updated forecast now sees a {run_position} run at {run_probability:.0%}."
                )
            else:
                bullets.append("The forecast has been recalculated for the new board.")

        if not bullets:
            bullets.append("The recommendation model will adapt to the player you selected.")

        summary = (
            f"You selected {selected} instead of {recommended}."
            if recommended
            else f"You selected {selected}."
        )
        return CoachMessage(
            message_type=CoachMessageType.DEVIATION,
            severity=CoachSeverity.WARNING,
            title="PICK REVIEW",
            summary=summary,
            bullets=tuple(bullets[: cls.MAX_BULLETS]),
            action="The next recommendation will use the updated roster and forecast.",
            recommended_player=recommended or None,
            selected_player=selected,
        )
