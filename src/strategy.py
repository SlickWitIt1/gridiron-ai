from dataclasses import dataclass
from enum import Enum


class DraftStrategy(Enum):
    UNDETERMINED = "Undetermined"
    BALANCED = "Balanced"
    HERO_RB = "Hero RB"
    ZERO_RB = "Zero RB"
    ROBUST_RB = "Robust RB"
    WR_HEAVY = "WR Heavy"
    ELITE_QB = "Elite QB"
    ELITE_TE = "Elite TE"


@dataclass(frozen=True, slots=True)
class StrategyScore:
    strategy: DraftStrategy
    score: int
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StrategyResult:
    primary_strategy: DraftStrategy
    secondary_strategy: DraftStrategy | None
    confidence: int
    next_priorities: tuple[str, ...]
    explanation: str
    scores: tuple[StrategyScore, ...]

    @property
    def strategy(self) -> DraftStrategy:
        """Backward-compatible alias for older callers."""
        return self.primary_strategy

    @property
    def next_priority(self) -> str:
        """Backward-compatible alias for older callers."""
        return self.next_priorities[0] if self.next_priorities else "Best Value"
