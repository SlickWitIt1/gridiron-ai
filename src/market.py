import random

from player import Player


class DraftMarket:
    def __init__(
        self,
        players: list[Player],
        seed: int | None = None,
    ):
        self.random = random.Random(seed)

        self.values = self._create_values(players)

        self.sorted_players = sorted(
            players,
            key=self.rank_for,
        )

    def _create_values(
        self,
        players: list[Player],
    ) -> dict[str, float]:
        values: dict[str, float] = {}

        for player in players:
            standard_deviation = min(
                18.0,
                max(2.5, player.rank * 0.10),
            )

            simulated_rank = self.random.gauss(
                mu=float(player.rank),
                sigma=standard_deviation,
            )

            values[player.name] = max(
                1.0,
                simulated_rank,
            )

        return values

    def rank_for(self, player: Player) -> float:
        return self.values.get(
            player.name,
            float(player.rank),
        )