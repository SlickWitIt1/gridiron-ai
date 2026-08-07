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


@dataclass(slots=True)
class StrategyResult:
    strategy: DraftStrategy
    confidence: int
    next_priority: str
    explanation: str