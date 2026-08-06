from player import Player
from player_scorer import PlayerScorer
from team import Team


class DecisionEngine:
    def __init__(self):
        self.player_scorer = PlayerScorer()

    def choose_player(
        self,
        team: Team,
        available_players: list[Player],
        approved_players: set[str] | None = None,
    ) -> Player | None:
        if not available_players:
            return None

        return max(
            available_players,
            key=lambda player: self.player_scorer.score_player(
                player=player,
                team=team,
                approved_players=approved_players,
            ),
        )