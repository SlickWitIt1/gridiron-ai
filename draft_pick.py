from dataclasses import dataclass

from player import Player


@dataclass
class DraftPick:

    overall: int
    round: int
    pick_in_round: int

    team: int

    player: Player