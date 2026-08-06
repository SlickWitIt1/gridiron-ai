from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationScore:
    """Explainable score components for one draft recommendation."""

    total: float

    projection: float
    wait_risk: float
    roster_fit: float
    scarcity: float
    tier_drop: float
    preference: float

    confidence: int

    @property
    def score(self) -> float:
        """Compatibility alias used by existing UI code."""
        return self.total
