from player import Player


class DraftBoard:

    def __init__(self, players: list[Player]):

        self.available_players = players.copy()

    def best_available(self) -> Player | None:

        if not self.available_players:
            return None

        return self.available_players[0]

    def draft_player(self, player: Player):

        self.available_players.remove(player)

    def remaining_players(self):

        return len(self.available_players)