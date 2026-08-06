from player import Player
from preferences import normalize_name
from team import Team, base_position


class PlayerScorer:
    MY_GUY_BONUS = 35.0
    STARTER_NEED_BONUS = 30.0

    BACKUP_QB_PENALTY = 45.0
    BACKUP_TE_PENALTY = 25.0
    EXTRA_DST_PENALTY = 250.0
    EXTRA_K_PENALTY = 250.0

    EARLY_DST_PENALTY = 500.0
    EARLY_K_PENALTY = 500.0

    MID_ROUND_DST_PENALTY = 180.0
    MID_ROUND_K_PENALTY = 180.0

    def score_player(
        self,
        player: Player,
        team: Team,
        current_round: int,
        approved_players: set[str] | None = None,
    ) -> float:
        position = base_position(player.position)

        if not team.can_draft(position):
            return float("-inf")

        score = 1000.0 - float(player.rank)

        if (
            approved_players is not None
            and normalize_name(player.name) in approved_players
        ):
            score += self.MY_GUY_BONUS

        if team.needs_position(position):
            score += self.STARTER_NEED_BONUS

        if position == "QB" and team.count_position("QB") >= 1:
            score -= self.BACKUP_QB_PENALTY

        if position == "TE" and team.count_position("TE") >= 1:
            score -= self.BACKUP_TE_PENALTY

        if position == "DST":
            if team.count_position("DST") >= 1:
                score -= self.EXTRA_DST_PENALTY

            if current_round <= 10:
                score -= self.EARLY_DST_PENALTY
            elif current_round <= 13:
                score -= self.MID_ROUND_DST_PENALTY

        if position == "K":
            if team.count_position("K") >= 1:
                score -= self.EXTRA_K_PENALTY

            if current_round <= 11:
                score -= self.EARLY_K_PENALTY
            elif current_round <= 14:
                score -= self.MID_ROUND_K_PENALTY

        return score