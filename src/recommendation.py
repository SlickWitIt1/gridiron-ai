from dataclasses import dataclass

from recommendation_score import RecommendationScore


@dataclass(frozen=True, slots=True)
class Recommendation:
    player_name: str
    position: str

    projected_points: float
    projection_advantage: float

    is_my_guy: bool

    available_now_probability: float
    survival_probability: float | None

    roster_fit_score: float
    roster_need: str

    tier_number: int
    tier_size: int
    players_remaining_in_tier: int
    tier_drop_points: float
    tier_urgency: str
    is_last_in_tier: bool

    expected_value_lost: float

    likely_take_next_player: str | None
    likely_pass_current_player: str | None
    likely_pass_next_player: str | None
    take_path_projected_points: float
    pass_path_projected_points: float
    opportunity_cost: float
    tier_disappearance_probability: float

    score_breakdown: RecommendationScore

    grade: str
    action: str

    reasons: tuple[str, ...]

    @property
    def score(self) -> float:
        """Preserve the existing recommendation.score API."""
        return self.score_breakdown.total

    @property
    def confidence(self) -> int:
        """Preserve the existing recommendation.confidence API."""
        return self.score_breakdown.confidence
