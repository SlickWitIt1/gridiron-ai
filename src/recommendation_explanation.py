from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationExplanation:
    """UI-ready, deterministic explanation of one recommendation."""

    headline: str
    stars: int
    action: str
    score_text: str
    tier_text: str
    survival_text: str
    pass_cost_text: str
    confidence_text: str
    reasons: tuple[str, ...]
    alternatives: tuple[str, ...]


class RecommendationExplanationBuilder:
    """Turn recommendation-engine facts into concise draft-day language."""

    MAX_REASONS = 4
    MAX_ALTERNATIVES = 3

    @classmethod
    def build(
        cls,
        recommendation,
        alternatives=(),
    ) -> RecommendationExplanation:
        score = float(getattr(recommendation, "score", 0.0))
        grade = str(getattr(recommendation, "grade", "") or "")
        action = str(getattr(recommendation, "action", "") or "NO CALL")

        survival = getattr(recommendation, "survival_probability", None)
        tier_number = int(getattr(recommendation, "tier_number", 0) or 0)
        remaining = int(
            getattr(recommendation, "players_remaining_in_tier", 0) or 0
        )
        opportunity_cost = float(
            getattr(recommendation, "opportunity_cost", 0.0) or 0.0
        )

        explanation = RecommendationExplanation(
            headline=cls._headline(score, grade),
            stars=cls._stars(score),
            action=cls._display_action(action, score),
            score_text=f"{score:.0f}/100",
            tier_text=cls._tier_text(tier_number, remaining),
            survival_text=(
                f"{survival:.0%}" if survival is not None else "N/A"
            ),
            pass_cost_text=(
                f"+{opportunity_cost:.1f} pts"
                if opportunity_cost > 0.0
                else (
                    f"{opportunity_cost:.1f} pts"
                    if opportunity_cost < 0.0
                    else "≈ even"
                )
            ),
            confidence_text=f"{int(getattr(recommendation, 'confidence', 0))}%",
            reasons=cls._reasons(recommendation),
            alternatives=cls._alternatives(alternatives),
        )
        return explanation

    @staticmethod
    def _display_action(engine_action: str, score: float) -> str:
        """Keep urgency language consistent with overall recommendation strength."""
        if score < 55:
            return "BETTER OPTIONS AVAILABLE"
        if score < 65:
            return "VIABLE IF NEEDED"
        if score < 75 and engine_action == "DRAFT NOW":
            return "WORTH CONSIDERING"
        return engine_action

    @staticmethod
    def _headline(score: float, grade: str) -> str:
        if score >= 90 or grade == "A+":
            return "ELITE PICK"
        if score >= 82 or grade == "A":
            return "STRONG PICK"
        if score >= 74 or grade == "B+":
            return "GOOD PICK"
        if score >= 65 or grade == "B":
            return "SOLID OPTION"
        if score >= 55:
            return "VIABLE PICK"
        return "LOW PRIORITY"

    @staticmethod
    def _stars(score: float) -> int:
        if score >= 90:
            return 5
        if score >= 80:
            return 4
        if score >= 70:
            return 3
        if score >= 60:
            return 2
        return 1

    @staticmethod
    def _tier_text(tier_number: int, remaining: int) -> str:
        if tier_number <= 0:
            return "N/A"
        if remaining <= 1:
            return f"T{tier_number} • LAST"
        return f"T{tier_number} • {remaining} left"

    @classmethod
    def _reasons(cls, recommendation) -> tuple[str, ...]:
        reasons: list[str] = []

        tier_number = int(getattr(recommendation, "tier_number", 0) or 0)
        remaining = int(
            getattr(recommendation, "players_remaining_in_tier", 0) or 0
        )
        is_last = bool(getattr(recommendation, "is_last_in_tier", False))
        tier_drop = float(
            getattr(recommendation, "tier_drop_points", 0.0) or 0.0
        )
        tier_disappearance = float(
            getattr(
                recommendation,
                "tier_disappearance_probability",
                0.0,
            )
            or 0.0
        )
        survival = getattr(recommendation, "survival_probability", None)
        opportunity_cost = float(
            getattr(recommendation, "opportunity_cost", 0.0) or 0.0
        )
        projection_advantage = float(
            getattr(recommendation, "projection_advantage", 0.0) or 0.0
        )
        roster_fit = float(
            getattr(recommendation, "roster_fit_score", 0.0) or 0.0
        )
        roster_need = str(
            getattr(recommendation, "roster_need", "") or ""
        ).strip()
        strategy_fit = str(
            getattr(recommendation, "strategy_fit_label", "") or ""
        ).strip()
        is_my_guy = bool(getattr(recommendation, "is_my_guy", False))

        if is_last and tier_number > 0:
            reasons.append(
                f"Last available player in Tier {tier_number}."
            )
        elif tier_number > 0 and remaining <= 2 and tier_drop > 0.0:
            reasons.append(
                f"Only {remaining} players remain in Tier {tier_number}; "
                f"next tier drops {tier_drop:.1f} projected pts."
            )
        elif tier_disappearance >= 0.70 and tier_number > 0:
            reasons.append(
                f"{tier_disappearance:.0%} chance Tier {tier_number} "
                "is gone by your next pick."
            )

        if survival is not None:
            if survival < 0.20:
                reasons.append(
                    f"Only {survival:.0%} chance he survives to your next pick."
                )
            elif survival < 0.40:
                reasons.append(
                    f"Meaningful wait risk: {survival:.0%} chance he makes it back."
                )
            elif survival >= 0.75:
                reasons.append(
                    f"Likely to survive: {survival:.0%} chance he reaches your next pick."
                )

        if opportunity_cost >= 5.0:
            reasons.append(
                f"Taking him now projects {opportunity_cost:.1f} more roster pts "
                "than the pass path."
            )
        elif opportunity_cost <= -5.0:
            reasons.append(
                f"Passing currently projects {abs(opportunity_cost):.1f} more roster pts."
            )

        if projection_advantage >= 10.0:
            reasons.append(
                f"Projects {projection_advantage:.1f} pts above positional replacement."
            )

        if roster_need and roster_fit >= 7.0:
            reasons.append(
                f"Strong roster fit: {roster_need}."
            )

        if strategy_fit and strategy_fit.upper() in {
            "ELITE",
            "EXCELLENT",
            "STRONG",
            "GREAT",
        }:
            reasons.append(
                f"Fits your current {getattr(recommendation, 'primary_strategy', 'draft')} build."
            )

        if is_my_guy:
            reasons.append("Matches your My Guys preference.")

        # Fall back to the engine's own reasons; no invented claims.
        for reason in tuple(getattr(recommendation, "reasons", ())):
            clean = str(reason).strip().lstrip("•").strip()
            if clean and clean not in reasons:
                reasons.append(clean)
            if len(reasons) >= cls.MAX_REASONS:
                break

        return tuple(reasons[: cls.MAX_REASONS])

    @classmethod
    def _alternatives(cls, alternatives) -> tuple[str, ...]:
        rows = []
        for rank, rec in enumerate(
            tuple(alternatives)[: cls.MAX_ALTERNATIVES],
            start=2,
        ):
            survival = getattr(rec, "survival_probability", None)
            survival_text = (
                f" • {survival:.0%} survives"
                if survival is not None
                else ""
            )
            rows.append(
                f"#{rank}  {rec.player_name}  •  "
                f"{float(rec.score):.0f}/100{survival_text}"
            )
        return tuple(rows)
