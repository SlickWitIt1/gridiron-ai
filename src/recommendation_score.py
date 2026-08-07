from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationScore:
    """Explainable score components for one draft recommendation.

    Every component is expressed in recommendation-score points, so the
    component values add directly to ``total``. The maxima sum to 100.
    """

    total: float

    projection: float
    wait_risk: float
    roster_fit: float
    scarcity: float
    tier_drop: float
    opportunity_cost: float
    strategy_fit: float
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
            + self.opportunity_cost
            + self.strategy_fit
            + self.preference
        )

    def component_items(self) -> tuple[tuple[str, float, float], ...]:
        """Return display name, earned points, and maximum points."""
        return (
            ("Projection", self.projection, 28.0),
            ("Wait Risk", self.wait_risk, 15.0),
            ("Roster Fit", self.roster_fit, 15.0),
            ("Scarcity", self.scarcity, 8.0),
            ("Tier Drop", self.tier_drop, 10.0),
            ("Opportunity Cost", self.opportunity_cost, 9.0),
            ("Strategy Fit", self.strategy_fit, 10.0),
            ("My Guy", self.preference, 5.0),
        )
