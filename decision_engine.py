from market import DraftMarket
from player import Player
from player_scorer import PlayerScorer
from preferences import normalize_name
from team import Team, base_position


class DecisionEngine:
    MARKET_CANDIDATE_WINDOW = 60
    POSITION_CANDIDATES = 8

    def __init__(self, market: DraftMarket):
        self.market = market
        self.player_scorer = PlayerScorer(market)

    def eligible_players(
        self,
        team: Team,
        available_players: list[Player],
    ) -> list[Player]:
        return [
            player
            for player in available_players
            if team.can_draft(
                base_position(player.position)
            )
        ]

    def candidate_players(
        self,
        team: Team,
        available_players: list[Player],
        approved_players: set[str] | None,
    ) -> list[Player]:
        eligible = self.eligible_players(
            team=team,
            available_players=available_players,
        )

        if not eligible:
            return []

        # Sort once using this simulation's randomized market.
        market_sorted = sorted(
            eligible,
            key=self.market.rank_for,
        )

        candidates = market_sorted[
            :self.MARKET_CANDIDATE_WINDOW
        ]

        # Always include strong options at positions that
        # still need to be filled, even if those positions
        # fall outside the general candidate window.
        needed_positions = {
            position
            for position in (
                "QB",
                "RB",
                "WR",
                "TE",
                "DST",
                "K",
            )
            if team.needs_position(position)
        }

        for position in needed_positions:
            position_players = [
                player
                for player in market_sorted
                if base_position(player.position) == position
            ]

            candidates.extend(
                position_players[
                    :self.POSITION_CANDIDATES
                ]
            )

        # Your preferred players must remain visible to the
        # decision engine even when their market rank is lower.
        if approved_players is not None:
            candidates.extend(
                player
                for player in eligible
                if normalize_name(player.name)
                in approved_players
            )

        # Remove duplicates while preserving order.
        unique_candidates: list[Player] = []
        seen_names: set[str] = set()

        for player in candidates:
            key = normalize_name(player.name)

            if key in seen_names:
                continue

            seen_names.add(key)
            unique_candidates.append(player)

        return unique_candidates

    def choose_player(
        self,
        team: Team,
        available_players: list[Player],
        current_round: int,
        approved_players: set[str] | None = None,
    ) -> Player | None:
        candidates = self.candidate_players(
            team=team,
            available_players=available_players,
            approved_players=approved_players,
        )

        if not candidates:
            return None

        player = max(
            candidates,
            key=lambda candidate: (
                self.player_scorer.score_player(
                    player=candidate,
                    team=team,
                    current_round=current_round,
                    approved_players=approved_players,
                )
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