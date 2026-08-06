from dataclasses import dataclass, field


@dataclass(slots=True)
class RecommendationScore:
    player_name: str

    total_score: float

    projection_score: float = 0.0
    wait_risk_score: float = 0.0
    roster_fit_score: float = 0.0
    scarcity_score: float = 0.0
    tier_drop_score: float = 0.0

    confidence: float = 0.0

    explanation: list[str] = field(default_factory=list)