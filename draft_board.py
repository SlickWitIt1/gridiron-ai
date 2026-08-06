from player import Player


class DraftBoard:
    def __init__(self, players: list[Player]):
        """
        players should already be sorted by FantasyPros rank.
        """

        self.original_players = players.copy()
        self.available_players = players.copy()

    def draft_player(self, player: Player):

        if player not in self.available_players:
            raise ValueError(f"{player.name} has already been drafted.")

        self.available_players.remove(player)

    def best_available(self):

        if not self.available_players:
            return None

        return self.available_players[0]

    def remaining(self):

        return len(self.available_players)

    def reset(self):

        self.available_players = self.original_players.copy()