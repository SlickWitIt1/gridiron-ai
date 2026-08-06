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

    def candidate_players(
        self,
        team: Team,
        available_names: set[str],
        approved_players: set[str] | None,
        excluded_players: set[str] | None = None,
    ) -> list[Player]:
        excluded_players = excluded_players or set()

        candidates: list[Player] = []

        position_counts: dict[str, int] = {
            "QB": 0,
            "RB": 0,
            "WR": 0,
            "TE": 0,
            "DST": 0,
            "K": 0,
        }

        needed_positions = {
            position
            for position in position_counts
            if team.needs_position(position)
        }

        for player in self.market.sorted_players:
            normalized_name = normalize_name(player.name)

            if player.name not in available_names:
                continue

            if normalized_name in excluded_players:
                continue

            position = base_position(player.position)

            if not team.can_draft(position):
                continue

            include_player = (
                len(candidates)
                < self.MARKET_CANDIDATE_WINDOW
            )

            if (
                position in needed_positions
                and position_counts[position]
                < self.POSITION_CANDIDATES
            ):
                include_player = True
                position_counts[position] += 1

            if (
                approved_players is not None
                and normalized_name in approved_players
            ):
                include_player = True

            if include_player:
                candidates.append(player)

            general_window_full = (
                len(candidates)
                >= self.MARKET_CANDIDATE_WINDOW
            )

            position_windows_full = all(
                position_counts[position]
                >= self.POSITION_CANDIDATES
                for position in needed_positions
            )

            if (
                approved_players is None
                and general_window_full
                and position_windows_full
            ):
                break

        return candidates

    def choose_player(
        self,
        team: Team,
        available_players: list[Player],
        current_round: int,
        approved_players: set[str] | None = None,
        available_names: set[str] | None = None,
        excluded_players: set[str] | None = None,
    ) -> Player | None:
        if not available_players:
            return None

        if available_names is None:
            available_names = {
                player.name
                for player in available_players
            }

        candidates = self.candidate_players(
            team=team,
            available_names=available_names,
            approved_players=approved_players,
            excluded_players=excluded_players,
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