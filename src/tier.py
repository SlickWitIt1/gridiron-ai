from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TierInfo:
    player_name: str
    position: str
    tier_number: int
    tier_size: int
    players_remaining: int
    projected_points: float
    drop_to_next_tier: float
    urgency: str
    is_last_in_tier: bool
