from market import DraftMarket
from player import Player
from player_scorer import PlayerScorer
from team import Team


class DecisionEngine:
    def __init__(self, market: DraftMarket):
        self.player_scorer = PlayerScorer(market)

    def choose_player(
        self,
        team: Team,
        available_players: list[Player],
        current_round: int,
        approved_players: set[str] | None = None,
    ) -> Player | None:
        if not available_players:
            return None

        player = max(
            available_players,
            key=lambda candidate: self.player_scorer.score_player(
                player=candidate,
                team=team,
                current_round=current_round,
                approved_players=approved_players,
            ),
        )

        score = self.player_scorer.score_player(
            player=player,
            team=team,
            current_round=current_round,
            approved_players=approved_players,
        )

        if score == float("-inf"):
            return None

        return player