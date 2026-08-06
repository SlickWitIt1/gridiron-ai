from player import Player


class Team:
    def __init__(self, team_id: int):
        self.team_id = team_id
        self.players = []

    def add_player(self, player: Player):
        self.players.append(player)

    def count_position(self, position_prefix: str) -> int:
        """
        Counts players by position.

        QB1 -> QB
        RB4 -> RB
        WR18 -> WR
        """
        return sum(
            1
            for p in self.players
            if p.position.startswith(position_prefix)
        )

    def has_player(self, name: str) -> bool:
        return any(p.name == name for p in self.players)

    def __str__(self):

        output = f"\nTeam {self.team_id}\n"
        output += "-" * 30 + "\n"

        for p in self.players:
            output += str(p) + "\n"

        return output