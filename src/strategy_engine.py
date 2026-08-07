from collections import Counter

from strategy import DraftStrategy, StrategyResult


class StrategyEngine:
    """Detect the draft strategy emerging from the user's roster."""

    def analyze(self, roster) -> StrategyResult:
        counts: Counter[str] = Counter()
        draft_order: list[str] = []

        for player in roster.players:
            position = player.position.upper().split("/")[0]
            counts[position] += 1
            draft_order.append(position)

        # Do not pretend we know the user's strategy before enough picks exist.
        if len(draft_order) < 2:
            return StrategyResult(
                strategy=DraftStrategy.UNDETERMINED,
                confidence=0,
                next_priority="Best Value",
                explanation="Not enough draft information yet.",
            )

        scores = {
            DraftStrategy.BALANCED: 0,
            DraftStrategy.HERO_RB: 0,
            DraftStrategy.ZERO_RB: 0,
            DraftStrategy.ROBUST_RB: 0,
            DraftStrategy.WR_HEAVY: 0,
            DraftStrategy.ELITE_QB: 0,
            DraftStrategy.ELITE_TE: 0,
        }

        # Hero RB:
        # One early anchor RB followed by investment elsewhere.
        if draft_order[0] == "RB":
            scores[DraftStrategy.HERO_RB] += 40

        if counts["RB"] == 1:
            scores[DraftStrategy.HERO_RB] += 20

        if counts["WR"] >= 2:
            scores[DraftStrategy.HERO_RB] += 15

        if counts["RB"] >= 2:
            scores[DraftStrategy.HERO_RB] -= 25

        # Zero RB:
        # No RB through at least the first three selections.
        if len(draft_order) >= 3 and counts["RB"] == 0:
            scores[DraftStrategy.ZERO_RB] += 70

        if (
            len(draft_order) >= 3
            and all(position != "RB" for position in draft_order[:3])
        ):
            scores[DraftStrategy.ZERO_RB] += 25

        # Robust RB:
        # Heavy early investment at running back.
        if counts["RB"] >= 2:
            scores[DraftStrategy.ROBUST_RB] += 35

        if counts["RB"] >= 3:
            scores[DraftStrategy.ROBUST_RB] += 45

        if len(draft_order) >= 3:
            early_rb_count = sum(
                position == "RB"
                for position in draft_order[:3]
            )
            scores[DraftStrategy.ROBUST_RB] += early_rb_count * 15

        # WR Heavy:
        # Multiple receivers taken early or a clearly receiver-dominant roster.
        if counts["WR"] >= 2:
            scores[DraftStrategy.WR_HEAVY] += 25

        if counts["WR"] >= 3:
            scores[DraftStrategy.WR_HEAVY] += 45

        if len(draft_order) >= 3:
            early_wr_count = sum(
                position == "WR"
                for position in draft_order[:3]
            )
            scores[DraftStrategy.WR_HEAVY] += early_wr_count * 12

        # Elite QB:
        # Quarterback selected very early.
        if draft_order[0] == "QB":
            scores[DraftStrategy.ELITE_QB] += 80
        elif len(draft_order) >= 2 and "QB" in draft_order[:2]:
            scores[DraftStrategy.ELITE_QB] += 60
        elif len(draft_order) >= 3 and "QB" in draft_order[:3]:
            scores[DraftStrategy.ELITE_QB] += 40

        # Elite TE:
        # Tight end selected very early.
        if draft_order[0] == "TE":
            scores[DraftStrategy.ELITE_TE] += 80
        elif len(draft_order) >= 2 and "TE" in draft_order[:2]:
            scores[DraftStrategy.ELITE_TE] += 60
        elif len(draft_order) >= 3 and "TE" in draft_order[:3]:
            scores[DraftStrategy.ELITE_TE] += 40

        # Balanced:
        # Reward positional diversity and discourage extreme concentration.
        filled_positions = sum(
            1
            for position in ("QB", "RB", "WR", "TE")
            if counts[position] > 0
        )

        scores[DraftStrategy.BALANCED] += filled_positions * 18

        if counts["RB"] in {1, 2}:
            scores[DraftStrategy.BALANCED] += 12

        if counts["WR"] in {1, 2}:
            scores[DraftStrategy.BALANCED] += 12

        if max(counts.values(), default=0) <= 2:
            scores[DraftStrategy.BALANCED] += 10

        best_strategy = max(scores, key=scores.get)
        best_score = scores[best_strategy]

        # If no strategy has enough evidence, keep it undetermined.
        if best_score < 35:
            return StrategyResult(
                strategy=DraftStrategy.UNDETERMINED,
                confidence=min(best_score, 34),
                next_priority="Best Value",
                explanation="The draft is still too early to identify a clear strategy.",
            )

        confidence = min(max(best_score, 0), 99)

        next_priorities = {
            DraftStrategy.BALANCED: "Best Value",
            DraftStrategy.HERO_RB: "WR",
            DraftStrategy.ZERO_RB: "RB",
            DraftStrategy.ROBUST_RB: "WR",
            DraftStrategy.WR_HEAVY: "RB",
            DraftStrategy.ELITE_QB: "RB or WR",
            DraftStrategy.ELITE_TE: "WR",
        }

        explanations = {
            DraftStrategy.BALANCED: (
                "Maintaining positional flexibility while taking value."
            ),
            DraftStrategy.HERO_RB: (
                "Built around one anchor running back while investing elsewhere."
            ),
            DraftStrategy.ZERO_RB: (
                "Delayed running backs in favor of premium pass catchers."
            ),
            DraftStrategy.ROBUST_RB: (
                "Invested heavily in running backs early."
            ),
            DraftStrategy.WR_HEAVY: (
                "Prioritized wide receivers to build weekly ceiling and depth."
            ),
            DraftStrategy.ELITE_QB: (
                "Secured a premium quarterback early."
            ),
            DraftStrategy.ELITE_TE: (
                "Secured a premium tight end early."
            ),
        }

        return StrategyResult(
            strategy=best_strategy,
            confidence=confidence,
            next_priority=next_priorities[best_strategy],
            explanation=explanations[best_strategy],
        )