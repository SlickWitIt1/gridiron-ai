from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoachMessage:
    command: str
    summary: str
    confidence_label: str
    tone: str
    key_points: tuple[str, ...]


class CoachMessageBuilder:
    """Translate recommendation facts into concise coach language.

    This layer never invents football facts. It only turns fields already
    produced by the recommendation/simulation stack into human-readable copy.
    """

    @classmethod
    def build(cls, recommendation, explanation) -> CoachMessage:
        confidence = int(getattr(recommendation, "confidence", 0) or 0)
        score = float(getattr(recommendation, "score", 0.0) or 0.0)
        player = str(getattr(recommendation, "player_name", "this player"))
        position = str(getattr(recommendation, "position", "") or "")
        survival = getattr(recommendation, "survival_probability", None)
        run_probability = float(
            getattr(recommendation, "position_run_probability", 0.0) or 0.0
        )
        expected_position_picks = float(
            getattr(recommendation, "expected_position_picks", 0.0) or 0.0
        )
        opportunity_cost = float(
            getattr(recommendation, "opportunity_cost", 0.0) or 0.0
        )
        tier_number = int(getattr(recommendation, "tier_number", 0) or 0)
        is_last = bool(getattr(recommendation, "is_last_in_tier", False))
        is_my_guy = bool(getattr(recommendation, "is_my_guy", False))
        roster_need = str(getattr(recommendation, "roster_need", "") or "")

        command, tone = cls._command(
            player=player,
            score=score,
            opportunity_cost=opportunity_cost,
            survival=survival,
        )

        sentences: list[str] = [command]

        leverage_bits: list[str] = []
        if is_last and tier_number > 0:
            leverage_bits.append(f"he's the last player in Tier {tier_number}")
        elif tier_number > 0:
            remaining = int(
                getattr(recommendation, "players_remaining_in_tier", 0) or 0
            )
            if remaining <= 2:
                leverage_bits.append(
                    f"only {remaining} players remain in Tier {tier_number}"
                )

        if survival is not None and survival < 0.25:
            leverage_bits.append(
                f"I only give him an {survival:.0%} chance to reach your next pick"
            )

        if expected_position_picks >= 2.5:
            leverage_bits.append(
                f"I project about {expected_position_picks:.1f} {position}s "
                "to go before you're back on the clock"
            )
        elif run_probability >= 0.45:
            leverage_bits.append(
                f"there's a {run_probability:.0%} chance of a {position} run"
            )

        if leverage_bits:
            leverage_sentence = cls._sentence_join(leverage_bits)
            sentences.append(
                leverage_sentence[:1].upper() + leverage_sentence[1:] + "."
            )

        value_bits: list[str] = []
        if opportunity_cost >= 3.0:
            value_bits.append(
                f"the take-now path leads the wait path by about "
                f"{opportunity_cost:.1f} projected roster points"
            )
        elif opportunity_cost <= -3.0:
            value_bits.append(
                f"the simulated wait path is actually ahead by about "
                f"{abs(opportunity_cost):.1f} projected roster points"
            )

        if roster_need in {"HIGH NEED", "GOOD FIT"}:
            value_bits.append(
                f"he also grades as a {roster_need.lower()} for your roster"
            )

        if is_my_guy:
            value_bits.append("he's also one of your My Guys")

        if value_bits:
            value_sentence = cls._sentence_join(value_bits)
            sentences.append(
                value_sentence[:1].upper() + value_sentence[1:] + "."
            )

        # Keep the default view short. The detailed deterministic reasons remain
        # available immediately underneath and in the advanced sections.
        summary = " ".join(sentences[:3])

        return CoachMessage(
            command=command,
            summary=summary,
            confidence_label=cls._confidence_label(confidence),
            tone=tone,
            key_points=tuple(explanation.reasons[:4]),
        )

    @staticmethod
    def _command(
        *,
        player: str,
        score: float,
        opportunity_cost: float,
        survival: float | None,
    ) -> tuple[str, str]:
        if score >= 88 or opportunity_cost >= 12.0:
            return f"I'd draft {player} here.", "aggressive"
        if score >= 78:
            return f"{player} is my pick.", "strong"
        if opportunity_cost <= -5.0 or (
            survival is not None and survival >= 0.80
        ):
            return f"I'd be comfortable waiting on {player}.", "patient"
        if score >= 66:
            return f"I lean {player}, but this one is close.", "lean"
        return f"I'd look at the alternatives before taking {player}.", "caution"

    @staticmethod
    def _confidence_label(confidence: int) -> str:
        if confidence >= 95:
            return "No-brainer"
        if confidence >= 88:
            return "Strong recommendation"
        if confidence >= 78:
            return "Preferred option"
        if confidence >= 68:
            return "Slight lean"
        if confidence >= 58:
            return "Close decision"
        return "Low conviction"

    @staticmethod
    def _sentence_join(parts: list[str]) -> str:
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return f"{parts[0]}, and {parts[1]}"
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"
