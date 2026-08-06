from dataclasses import dataclass


@dataclass
class Player:
    rank: int
    tier: int

    name: str
    position: str
    team: str
    bye: int

    upside: str
    bust: str
    sos: str

    drafted = False

    def __str__(self):
        return f"{self.rank:>3} | {self.position:<3} | {self.name}"