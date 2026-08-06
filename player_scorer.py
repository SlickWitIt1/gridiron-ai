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


class PlayerScorer:
    MY_GUY_BONUS = 35.0
    STARTER_NEED_BONUS = 20.0

    def score_player(
        self,
        player: Player,
        team: Team,
        approved_players: set[str] | None = None,
    ) -> float:
        position = base_position(player.position)

        # Lower FantasyPros rank is better.
        score = 1000.0 - float(player.rank)

        # Strongly favor approved players for the user's team.
        if (
            approved_players is not None
            and normalize_name(player.name) in approved_players
        ):
            score += self.MY_GUY_BONUS

        # Reward filling an open starting position.
        if team.needs_position(position):
            score += self.STARTER_NEED_BONUS

        # Avoid unnecessary backup QBs and TEs.
        if position == "QB" and team.count_position("QB") >= 1:
            score -= 30.0

        if position == "TE" and team.count_position("TE") >= 1:
            score -= 18.0

        # Avoid loading up on kickers or defenses.
        if position == "K" and team.count_position("K") >= 1:
            score -= 100.0

        if position == "DST" and team.count_position("DST") >= 1:
            score -= 100.0

        return score