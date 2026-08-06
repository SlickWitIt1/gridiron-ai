from player import Player


class Team:

    def __init__(self, number: int):

        self.number = number
        self.players = []

    def add_player(self, player: Player):

        self.players.append(player)

    def count_position(self, position: str):

        return sum(
            1 for player in self.players
            if player.position.startswith(position)
        )

    def needs_position(self, position: str):

        limits = {
            "QB": 1,
            "RB": 2,
            "WR": 2,
            "TE": 1,
        }

        if position not in limits:
            return True

        return self.count_position(position) < limits[position]

    def print_roster(self):

        print("\n" + "=" * 35)
        print(f"TEAM {self.number}")
        print("=" * 35)

        for player in self.players:
            print(player)

    def __str__(self):

        return f"Team {self.number}"