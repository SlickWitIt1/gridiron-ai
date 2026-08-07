from dataclasses import dataclass

from player import Player


@dataclass(frozen=True, slots=True)
class DraftPick:
    overall: int
    round_number: int
    pick_in_round: int
    team_number: int
    player: Player

    def __str__(self) -> str:
        return (
            f"Pick {self.overall:>3} | "
            f"Round {self.round_number:>2}.{self.pick_in_round:<2} | "
            f"Team {self.team_number:>2} | "
            f"{self.player}"
        )