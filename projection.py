from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Projection:
    name: str
    position: str
    team: str
    fantasy_points: float
    stats: dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.position:<3} | "
            f"{self.name:<25} | "
            f"{self.fantasy_points:>6.1f} projected points"
        )