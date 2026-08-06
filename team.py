from player import Player


class Team:

    def __init__(self, number: int):

        self.number = number
        self.players = []

    def add_player(self, player: Player):

        self.players.append(player)

    def __str__(self):

        return f"Team {self.number}"