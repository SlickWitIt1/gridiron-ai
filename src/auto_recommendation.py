from __future__ import annotations

from dataclasses import dataclass

from preferences import normalize_name
from projection_loader import load_projections
from team import base_position


@dataclass(frozen=True, slots=True)
class CandidatePool:
    player_names: tuple[str, ...]
    scanned_players: int
    legal_players: int


class AutoRecommendationCandidateBuilder:
    """Scan the whole board, then deep-analyze only serious candidates."""

    MAX_CANDIDATES = 20
    CORE_POSITIONS = ("QB", "RB", "WR", "TE")

    def __init__(self, projections=None, approved_players: set[str] | None = None) -> None:
        self.projections = projections or load_projections()
        self.approved_players = approved_players or set()

    def build(self, session) -> CandidatePool:
        available = list(session.available_players())
        team = session.state.user_team

        legal = [
            player for player in available
            if team.can_draft(base_position(player.position))
        ]

        core_filled = sum(
            min(team.count_position(position), required)
            for position, required in {"QB": 1, "RB": 2, "WR": 2, "TE": 1}.items()
        )
        allow_specialists = session.current_pick >= 120 or core_filled >= 6

        serious = [
            player for player in legal
            if base_position(player.position) in self.CORE_POSITIONS or allow_specialists
        ] or legal

        by_rank = sorted(
            serious,
            key=lambda player: (
                int(getattr(player, "rank", 9999) or 9999),
                -self._projection(player),
            ),
        )

        selected: dict[str, object] = {}

        def add(player) -> None:
            selected.setdefault(normalize_name(player.name), player)

        for player in by_rank[:10]:
            add(player)

        for position in self.CORE_POSITIONS:
            position_players = [
                player for player in serious
                if base_position(player.position) == position
            ]
            for player in position_players[:3]:
                add(player)

        for position in self.CORE_POSITIONS:
            if not team.needs_position(position):
                continue
            need_players = sorted(
                (
                    player for player in serious
                    if base_position(player.position) == position
                ),
                key=lambda player: (
                    -self._projection(player),
                    int(getattr(player, "rank", 9999) or 9999),
                ),
            )
            for player in need_players[:3]:
                add(player)

        best_rank = int(getattr(by_rank[0], "rank", 1) or 1) if by_rank else 1
        for player in serious:
            if normalize_name(player.name) not in self.approved_players:
                continue
            rank = int(getattr(player, "rank", 9999) or 9999)
            if rank <= best_rank + 40:
                add(player)

        if allow_specialists:
            for position in ("DST", "K"):
                if not team.needs_position(position):
                    continue
                position_players = [
                    player for player in serious
                    if base_position(player.position) == position
                ]
                if position_players:
                    add(position_players[0])

        ordered = sorted(
            selected.values(),
            key=lambda player: self._prescore(player, team, best_rank),
            reverse=True,
        )

        return CandidatePool(
            player_names=tuple(
                player.name for player in ordered[: self.MAX_CANDIDATES]
            ),
            scanned_players=len(available),
            legal_players=len(legal),
        )

    def _projection(self, player) -> float:
        projection = self.projections.get(normalize_name(player.name))
        return float(projection.fantasy_points) if projection is not None else 0.0

    def _prescore(self, player, team, best_rank: int) -> float:
        position = base_position(player.position)
        rank = int(getattr(player, "rank", 9999) or 9999)
        tier = int(getattr(player, "tier", 99) or 99)

        return (
            max(0.0, 45.0 - max(0, rank - best_rank) * 1.5)
            + max(0.0, 20.0 - max(0, tier - 1) * 3.0)
            + (18.0 if team.needs_position(position) else 0.0)
            + (
                12.0
                if normalize_name(player.name) in self.approved_players
                else 0.0
            )
            + min(12.0, self._projection(player) / 30.0)
        )
