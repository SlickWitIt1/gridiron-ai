from player import Player
from team import Team


class DecisionEngine:

    def choose_player(self, team: Team, available_players: list[Player]):

        for player in available_players:

            position = player.position[:2]

            if team.needs_position(position):
                return player

        return available_players[0]