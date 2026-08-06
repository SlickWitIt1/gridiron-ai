from player import Player
from preferences import normalize_name
from team import Team


def base_position(position: str) -> str:
    position = position.upper().strip()

    if position.startswith("DST") or position.startswith("DEF"):
        return "DST"

    if position.startswith("QB"):
        return "QB"

    if position.startswith("RB"):
        return "RB"

    if position.startswith("WR"):
        return "WR"

    if position.startswith("TE"):
        return "TE"

    if position.startswith("K"):
        return "K"

    return position


class DecisionEngine:
    def choose_player(
        self,
        team: Team,
        available_players: list[Player],
        approved_players: set[str] | None = None,
    ) -> Player | None:
        if not available_players:
            return None

        candidate_players = available_players

        if approved_players is not None:
            candidate_players = [
                player
                for player in available_players
                if normalize_name(player.name) in approved_players
            ]

            if not candidate_players:
                return None

        # First, fill positions still needed in the starting lineup.
        for player in candidate_players:
            position = base_position(player.position)

            if team.needs_position(position):
                return player

        # Once starter needs are filled, take the best-ranked
        # remaining eligible player for the bench.
        return candidate_players[0]