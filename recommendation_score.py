from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationScore:
    """Explainable score components for one draft recommendation.

    Every component is already expressed in recommendation-score points,
    so the component values add directly to ``total``.
    """

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

    @property
    def components_total(self) -> float:
        return (
            self.projection
            + self.wait_risk
            + self.roster_fit
            + self.scarcity
            + self.tier_drop
            + self.preference
        )

    def component_items(self) -> tuple[tuple[str, float, float], ...]:
        """Return display name, earned points, and maximum points."""
        return (
            ("Projection", self.projection, 35.0),
            ("Wait Risk", self.wait_risk, 20.0),
            ("Roster Fit", self.roster_fit, 15.0),
            ("Scarcity", self.scarcity, 10.0),
            ("Tier Drop", self.tier_drop, 15.0),
            ("My Guy", self.preference, 5.0),
        )
