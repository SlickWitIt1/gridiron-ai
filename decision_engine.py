from player import Player
from team import Team


class DecisionEngine:

    def choose_player(self, team: Team, available_players: list[Player]) -> Player | None:

        for player in available_players:

            position = player.position[:2]

            if team.needs_position(position):
                return player

        if not available_players:
            return None

        return available_players[0]