from player import Player


class DraftBoard:
    def __init__(
        self,
        players: list[Player],
    ):
        self.available_players = players.copy()

        self.available_names = {
            player.name
            for player in players
        }

    def best_available(self) -> Player | None:
        if not self.available_players:
            return None

        return self.available_players[0]

    def draft_player(self, player: Player) -> None:
        if player.name not in self.available_names:
            raise ValueError(
                f"{player.name} has already been drafted."
            )

        self.available_names.remove(player.name)
        self.available_players.remove(player)

    def is_available(self, player: Player) -> bool:
        return player.name in self.available_names

    def remaining_players(self) -> int:
        return len(self.available_players)