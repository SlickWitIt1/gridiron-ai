from config import (
    FLEX_ELIGIBLE_POSITIONS,
    FLEX_SLOTS,
    POSITION_MAXIMUMS,
    ROSTER_SIZE,
    STARTER_REQUIREMENTS,
)
from player import Player


def base_position(position: str) -> str:
    normalized = position.upper().strip()

    if normalized.startswith("DST") or normalized.startswith("DEF"):
        return "DST"

    for position_name in ("QB", "RB", "WR", "TE", "K"):
        if normalized.startswith(position_name):
            return position_name

    return normalized


class Team:
    def __init__(self, number: int):
        self.number = number
        self.players: list[Player] = []

    def add_player(self, player: Player) -> None:
        position = base_position(player.position)

        if not self.can_draft(position):
            raise ValueError(
                f"Team {self.number} cannot draft another {position}."
            )

        self.players.append(player)

    def count_position(self, position: str) -> int:
        return sum(
            1
            for player in self.players
            if base_position(player.position) == position
        )

    def can_draft(self, position: str) -> bool:
        if len(self.players) >= ROSTER_SIZE:
            return False

        maximum = POSITION_MAXIMUMS.get(position)

        if maximum is None:
            return False

        return self.count_position(position) < maximum

    def core_starter_slots_filled(self) -> int:
        return sum(
            min(
                self.count_position(position),
                required,
            )
            for position, required in STARTER_REQUIREMENTS.items()
        )

    def flex_slots_filled(self) -> int:
        eligible_players = sum(
            self.count_position(position)
            for position in FLEX_ELIGIBLE_POSITIONS
        )

        core_eligible_slots = sum(
            min(
                self.count_position(position),
                STARTER_REQUIREMENTS[position],
            )
            for position in FLEX_ELIGIBLE_POSITIONS
        )

        eligible_surplus = max(
            0,
            eligible_players - core_eligible_slots,
        )

        return min(FLEX_SLOTS, eligible_surplus)

    def starter_slots_filled(self) -> int:
        return (
            self.core_starter_slots_filled()
            + self.flex_slots_filled()
        )

    def needs_position(self, position: str) -> bool:
        if not self.can_draft(position):
            return False

        required = STARTER_REQUIREMENTS.get(position, 0)

        if self.count_position(position) < required:
            return True

        if (
            position in FLEX_ELIGIBLE_POSITIONS
            and self.flex_slots_filled() < FLEX_SLOTS
        ):
            return True

        return False

    def bench_players(self) -> int:
        return max(
            0,
            len(self.players) - self.starter_slots_filled(),
        )

    def is_complete(self) -> bool:
        return len(self.players) == ROSTER_SIZE

    def print_roster(self) -> None:
        print("\n" + "=" * 35)
        print(f"TEAM {self.number}")
        print("=" * 35)

        for player in self.players:
            print(player)

        print("-" * 35)
        print(f"Players: {len(self.players)}/{ROSTER_SIZE}")
        print(f"Starter slots filled: {self.starter_slots_filled()}/9")
        print(f"Bench players: {self.bench_players()}/7")

    def __str__(self) -> str:
        return f"Team {self.number}"