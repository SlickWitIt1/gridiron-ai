from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CostOfWaitingView:
    headline: str
    risk_level: str
    pick_window: str
    survival_text: str
    tier_risk_text: str
    point_swing_text: str
    point_swing_detail: str
    take_path_text: str
    pass_path_text: str


class CostOfWaitingBuilder:
    """Turn simulator-produced wait analysis into compact draft-day language."""

    @classmethod
    def build(
        cls,
        recommendation,
        *,
        current_pick: int | None,
        next_pick: int | None,
    ) -> CostOfWaitingView:
        if next_pick is None:
            return CostOfWaitingView(
                headline="FINAL PICK — NO WAIT DECISION",
                risk_level="neutral",
                pick_window=cls._pick_window(current_pick, next_pick),
                survival_text="N/A",
                tier_risk_text="N/A",
                point_swing_text="N/A",
                point_swing_detail="There is no later user pick to preserve value for.",
                take_path_text=f"TAKE: {getattr(recommendation, 'player_name', 'Best available player')}",
                pass_path_text="WAIT: not applicable",
            )

        survival = getattr(recommendation, "survival_probability", None)
        tier_risk = float(
            getattr(
                recommendation,
                "tier_disappearance_probability",
                0.0,
            )
            or 0.0
        )
        opportunity_cost = float(
            getattr(recommendation, "opportunity_cost", 0.0)
            or 0.0
        )

        headline, risk_level = cls._headline(
            survival=survival,
            tier_risk=tier_risk,
            opportunity_cost=opportunity_cost,
        )

        pick_window = cls._pick_window(current_pick, next_pick)

        take_points = float(
            getattr(
                recommendation,
                "take_path_projected_points",
                0.0,
            )
            or 0.0
        )
        pass_points = float(
            getattr(
                recommendation,
                "pass_path_projected_points",
                0.0,
            )
            or 0.0
        )

        likely_take_next = getattr(
            recommendation,
            "likely_take_next_player",
            None,
        )
        likely_pass_current = getattr(
            recommendation,
            "likely_pass_current_player",
            None,
        )
        likely_pass_next = getattr(
            recommendation,
            "likely_pass_next_player",
            None,
        )

        return CostOfWaitingView(
            headline=headline,
            risk_level=risk_level,
            pick_window=pick_window,
            survival_text=(
                f"{survival:.0%}"
                if survival is not None
                else "N/A"
            ),
            tier_risk_text=f"{tier_risk:.0%}",
            point_swing_text=cls._point_swing_text(opportunity_cost),
            point_swing_detail=cls._point_swing_detail(opportunity_cost),
            take_path_text=cls._path_text(
                label="TAKE",
                current_player=getattr(
                    recommendation,
                    "player_name",
                    None,
                ),
                next_player=likely_take_next,
                points=take_points,
            ),
            pass_path_text=cls._path_text(
                label="WAIT",
                current_player=likely_pass_current,
                next_player=likely_pass_next,
                points=pass_points,
            ),
        )

    @staticmethod
    def _headline(
        *,
        survival: float | None,
        tier_risk: float,
        opportunity_cost: float,
    ) -> tuple[str, str]:
        # Use only simulator-derived facts. Opportunity cost is the strongest
        # signal because it compares full simulated roster paths.
        if opportunity_cost >= 8.0:
            return "EXPENSIVE TO WAIT", "high"
        if survival is not None and survival < 0.20:
            return "HIGH RISK TO WAIT", "high"
        if tier_risk >= 0.75:
            return "TIER MAY DISAPPEAR", "high"

        if opportunity_cost >= 3.0:
            return "LEAN TAKE NOW", "medium"
        if survival is not None and survival < 0.45:
            return "MEANINGFUL WAIT RISK", "medium"
        if tier_risk >= 0.50:
            return "TIER AT RISK", "medium"

        if opportunity_cost <= -3.0:
            return "WAIT PATH LEADS", "safe"
        if survival is not None and survival >= 0.75:
            return "LIKELY SAFE TO WAIT", "safe"

        return "WAIT DECISION IS CLOSE", "neutral"

    @staticmethod
    def _pick_window(
        current_pick: int | None,
        next_pick: int | None,
    ) -> str:
        if current_pick is None:
            return "PICK —"
        if next_pick is None:
            return f"PICK {current_pick} • FINAL USER PICK"
        picks_between = max(0, next_pick - current_pick - 1)
        return (
            f"PICK {current_pick} → {next_pick}  •  "
            f"{picks_between} selections in between"
        )

    @staticmethod
    def _point_swing_text(opportunity_cost: float) -> str:
        if opportunity_cost > 0.0:
            return f"+{opportunity_cost:.1f}"
        if opportunity_cost < 0.0:
            return f"{opportunity_cost:.1f}"
        return "≈0"

    @staticmethod
    def _point_swing_detail(opportunity_cost: float) -> str:
        if opportunity_cost >= 1.0:
            return "projected pts favor taking him now"
        if opportunity_cost <= -1.0:
            return "projected pts favor waiting"
        return "projected roster paths are nearly even"

    @staticmethod
    def _path_text(
        *,
        label: str,
        current_player: str | None,
        next_player: str | None,
        points: float,
    ) -> str:
        names = [
            name
            for name in (current_player, next_player)
            if name
        ]
        player_text = " + ".join(names) if names else "No clear simulated pair"

        if points > 0.0:
            return f"{label}: {player_text}  •  {points:.1f} pts"
        return f"{label}: {player_text}"
