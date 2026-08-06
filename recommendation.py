from dataclasses import dataclass


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

    tier_drop_points: float
    expected_value_lost: float
    confidence: int

    score: float
    grade: str
    action: str

    reasons: tuple[str, ...]
