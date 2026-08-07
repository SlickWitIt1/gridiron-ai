from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from draft_pick import DraftPick
from player import Player
from strategy import DraftStrategy, StrategyResult, StrategyScore
from team import Team, base_position


@dataclass(frozen=True, slots=True)
class _PickContext:
    player: Player
    round_number: int
    overall: int

    @property
    def position(self) -> str:
        return base_position(self.player.position)


class StrategyEngine:
    """Infer the user's emerging draft build from timing and player quality.

    The engine uses independent detectors, then compares their scores. It does
    not force a strategy when evidence is weak or competing strategies are too
    close.
    """

    MIN_PICKS_FOR_DETECTION = 3
    MIN_PRIMARY_SCORE = 45

    # Stable order used only to make exact ties deterministic. A tied result is
    # still reported with low confidence and a secondary strategy.
    STRATEGY_ORDER = (
        DraftStrategy.HERO_RB,
        DraftStrategy.ZERO_RB,
        DraftStrategy.ROBUST_RB,
        DraftStrategy.WR_HEAVY,
        DraftStrategy.ELITE_QB,
        DraftStrategy.ELITE_TE,
        DraftStrategy.BALANCED,
    )

    def analyze(
        self,
        roster: Team,
        draft_picks: Iterable[DraftPick] | None = None,
    ) -> StrategyResult:
        picks = self._pick_contexts(roster, draft_picks)

        if len(picks) < self.MIN_PICKS_FOR_DETECTION:
            return self._undetermined(
                explanation=(
                    "Still learning your draft strategy. At least three of "
                    "your selections are needed for a dependable read."
                )
            )

        scores = (
            self._detect_hero_rb(picks),
            self._detect_zero_rb(picks),
            self._detect_robust_rb(picks),
            self._detect_wr_heavy(picks),
            self._detect_elite_qb(picks),
            self._detect_elite_te(picks),
            self._detect_balanced(picks),
        )

        order_index = {
            strategy: index
            for index, strategy in enumerate(self.STRATEGY_ORDER)
        }
        ranked = sorted(
            scores,
            key=lambda item: (-item.score, order_index[item.strategy]),
        )

        primary = ranked[0]
        secondary = ranked[1]

        if primary.score < self.MIN_PRIMARY_SCORE:
            return self._undetermined(
                explanation=(
                    "No draft strategy has enough evidence yet. Keep taking "
                    "value while the build develops."
                ),
                scores=tuple(ranked),
            )

        margin = primary.score - secondary.score
        confidence = self._confidence(primary.score, margin, len(picks))
        priorities = self._priorities(
            strategy=primary.strategy,
            picks=picks,
            roster=roster,
        )
        explanation = self._explanation(primary, secondary, margin)

        return StrategyResult(
            primary_strategy=primary.strategy,
            secondary_strategy=secondary.strategy,
            confidence=confidence,
            next_priorities=priorities,
            explanation=explanation,
            scores=tuple(ranked),
        )

    @staticmethod
    def _pick_contexts(
        roster: Team,
        draft_picks: Iterable[DraftPick] | None,
    ) -> list[_PickContext]:
        if draft_picks is not None:
            user_picks = [
                pick
                for pick in draft_picks
                if pick.team_number == roster.number
            ]
            user_picks.sort(key=lambda pick: pick.overall)
            return [
                _PickContext(
                    player=pick.player,
                    round_number=pick.round_number,
                    overall=pick.overall,
                )
                for pick in user_picks
            ]

        # Backward-compatible fallback. Team.players currently preserves add
        # order, but callers should pass DraftPick history whenever available.
        return [
            _PickContext(
                player=player,
                round_number=index,
                overall=index,
            )
            for index, player in enumerate(roster.players, start=1)
        ]

    @staticmethod
    def _position_rank(player: Player) -> int | None:
        text = player.position.upper().strip()
        digits = "".join(character for character in text if character.isdigit())
        return int(digits) if digits else None

    @classmethod
    def _is_anchor_rb(cls, player: Player) -> bool:
        position_rank = cls._position_rank(player)
        return (
            base_position(player.position) == "RB"
            and (
                player.rank <= 24
                or player.tier <= 2
                or (position_rank is not None and position_rank <= 10)
            )
        )

    @classmethod
    def _is_elite_qb(cls, player: Player) -> bool:
        position_rank = cls._position_rank(player)
        return (
            base_position(player.position) == "QB"
            and (
                player.rank <= 40
                or player.tier <= 2
                or (position_rank is not None and position_rank <= 5)
            )
        )

    @classmethod
    def _is_elite_te(cls, player: Player) -> bool:
        position_rank = cls._position_rank(player)
        return (
            base_position(player.position) == "TE"
            and (
                player.rank <= 36
                or player.tier <= 2
                or (position_rank is not None and position_rank <= 4)
            )
        )

    @staticmethod
    def _count(picks: list[_PickContext], position: str, through: int | None = None) -> int:
        sample = picks if through is None else picks[:through]
        return sum(pick.position == position for pick in sample)

    def _detect_hero_rb(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        score = 0
        first_four = picks[:4]
        early_rbs = [pick for pick in first_four if pick.position == "RB"]

        if early_rbs and early_rbs[0].round_number <= 2 and self._is_anchor_rb(early_rbs[0].player):
            score += 55
            evidence.append("An anchor-quality RB was selected in the first two rounds.")

        if len(early_rbs) == 1:
            score += 22
            evidence.append("Only one RB was taken through the first four selections.")
        elif len(early_rbs) >= 2:
            score -= 38

        non_rb_after_anchor = sum(
            pick.position != "RB"
            for pick in picks[1:5]
        )
        if non_rb_after_anchor >= 3:
            score += 18
            evidence.append("The following picks were invested outside RB.")

        return StrategyScore(DraftStrategy.HERO_RB, self._clamp_score(score), tuple(evidence))

    def _detect_zero_rb(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        score = 0
        first_four_rb = self._count(picks, "RB", through=4)
        first_five_rb = self._count(picks, "RB", through=5)

        if len(picks) >= 4 and first_four_rb == 0:
            score += 72
            evidence.append("No RB was selected through the first four picks.")
        if len(picks) >= 5 and first_five_rb == 0:
            score += 18
            evidence.append("The RB fade continued through five picks.")

        premium_pass_catchers = sum(
            pick.position in {"WR", "TE"}
            for pick in picks[:5]
        )
        if premium_pass_catchers >= 4:
            score += 10
            evidence.append("Early capital was concentrated at WR/TE.")

        if first_four_rb >= 1:
            score -= 55

        return StrategyScore(DraftStrategy.ZERO_RB, self._clamp_score(score), tuple(evidence))

    def _detect_robust_rb(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        score = 0
        rb_first_three = self._count(picks, "RB", through=3)
        rb_first_five = self._count(picks, "RB", through=5)

        if rb_first_three >= 2:
            score += 58
            evidence.append("At least two RBs were taken in the first three picks.")
        if rb_first_five >= 3:
            score += 34
            evidence.append("Three RBs were secured within the first five picks.")
        if rb_first_three == 0:
            score -= 35

        return StrategyScore(DraftStrategy.ROBUST_RB, self._clamp_score(score), tuple(evidence))

    def _detect_wr_heavy(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        score = 0
        wr_first_four = self._count(picks, "WR", through=4)
        wr_first_five = self._count(picks, "WR", through=5)
        total_wr = self._count(picks, "WR")

        if wr_first_four >= 3:
            score += 64
            evidence.append("Three WRs were taken within the first four picks.")
        elif wr_first_five >= 3:
            score += 52
            evidence.append("Three WRs were taken within the first five picks.")

        if total_wr >= 4:
            score += 20
            evidence.append("The roster has accumulated four or more WRs.")

        if total_wr / len(picks) >= 0.60:
            score += 16
            evidence.append("At least 60% of selections are WRs.")

        return StrategyScore(DraftStrategy.WR_HEAVY, self._clamp_score(score), tuple(evidence))

    def _detect_elite_qb(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        score = 0

        for pick in picks:
            if pick.position != "QB":
                continue
            if pick.round_number <= 3 and self._is_elite_qb(pick.player):
                score = 82 if pick.round_number <= 2 else 68
                evidence.append(
                    f"An elite-quality QB was selected in Round {pick.round_number}."
                )
            elif pick.round_number <= 3:
                score = 22
                evidence.append("A QB was selected early, but not at an elite threshold.")
            break

        return StrategyScore(DraftStrategy.ELITE_QB, self._clamp_score(score), tuple(evidence))

    def _detect_elite_te(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        score = 0

        for pick in picks:
            if pick.position != "TE":
                continue
            if pick.round_number <= 3 and self._is_elite_te(pick.player):
                score = 82 if pick.round_number <= 2 else 68
                evidence.append(
                    f"An elite-quality TE was selected in Round {pick.round_number}."
                )
            elif pick.round_number <= 3:
                score = 22
                evidence.append("A TE was selected early, but not at an elite threshold.")
            break

        return StrategyScore(DraftStrategy.ELITE_TE, self._clamp_score(score), tuple(evidence))

    def _detect_balanced(self, picks: list[_PickContext]) -> StrategyScore:
        evidence: list[str] = []
        counts = Counter(pick.position for pick in picks)
        core_positions = {position for position in ("QB", "RB", "WR", "TE") if counts[position]}
        score = 0

        if len(core_positions) >= 3:
            score += 42
            evidence.append("At least three core positions have been addressed.")
        if counts["RB"] >= 1 and counts["WR"] >= 1:
            score += 18
            evidence.append("Both RB and WR have early investment.")
        if max(counts.values(), default=0) <= 2:
            score += 18
            evidence.append("No position has been heavily concentrated.")
        if len(picks) >= 4 and len(core_positions) >= 4:
            score += 18
            evidence.append("All four core positions are represented.")

        return StrategyScore(DraftStrategy.BALANCED, self._clamp_score(score), tuple(evidence))

    @staticmethod
    def _confidence(primary_score: int, margin: int, pick_count: int) -> int:
        evidence_strength = max(0.0, min(1.0, (primary_score - 35) / 65))
        separation = max(0.0, min(1.0, margin / 45))
        sample_strength = max(0.0, min(1.0, (pick_count - 2) / 6))
        confidence = (
            evidence_strength * 45
            + separation * 40
            + sample_strength * 15
        )
        return round(max(1.0, min(99.0, confidence)))

    def _priorities(
        self,
        strategy: DraftStrategy,
        picks: list[_PickContext],
        roster: Team,
    ) -> tuple[str, ...]:
        current_round = picks[-1].round_number
        counts = Counter(pick.position for pick in picks)

        if strategy == DraftStrategy.ZERO_RB:
            if current_round < 6:
                return ("Best Value", "WR/TE", "RB only at strong tier value")
            return ("RB", "Best Value", "WR depth")
        if strategy == DraftStrategy.HERO_RB:
            return ("WR", "TE or QB value", "Second RB only at tier value")
        if strategy == DraftStrategy.ROBUST_RB:
            return ("WR", "TE/QB value", "Avoid another RB unless exceptional")
        if strategy == DraftStrategy.WR_HEAVY:
            return ("RB", "QB/TE value", "Best Value")
        if strategy == DraftStrategy.ELITE_QB:
            return ("RB/WR", "TE value", "Best Value")
        if strategy == DraftStrategy.ELITE_TE:
            return ("RB/WR", "QB value", "Best Value")

        needs = [
            position
            for position in ("RB", "WR", "QB", "TE")
            if roster.needs_position(position)
        ]
        if needs:
            return tuple(needs[:2] + ["Best Value"])
        return ("Best Value", "Tier Value", "Depth")

    @staticmethod
    def _explanation(
        primary: StrategyScore,
        secondary: StrategyScore,
        margin: int,
    ) -> str:
        lead_text = (
            "clear"
            if margin >= 25
            else "moderate"
            if margin >= 10
            else "narrow"
        )
        primary_evidence = primary.evidence[0] if primary.evidence else "The roster pattern supports this build."
        return (
            f"{primary.strategy.value} is the primary build with a {lead_text} "
            f"lead over {secondary.strategy.value}. {primary_evidence}"
        )

    @staticmethod
    def _clamp_score(score: int) -> int:
        return max(0, min(100, score))

    @staticmethod
    def _undetermined(
        explanation: str,
        scores: tuple[StrategyScore, ...] = (),
    ) -> StrategyResult:
        return StrategyResult(
            primary_strategy=DraftStrategy.UNDETERMINED,
            secondary_strategy=None,
            confidence=0,
            next_priorities=("Best Value",),
            explanation=explanation,
            scores=scores,
        )
