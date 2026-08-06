from dataclasses import dataclass

from player import Player
from preferences import normalize_name
from projection import Projection
from team import Team, base_position


@dataclass(frozen=True, slots=True)
class LineupSelection:
    slot: str
    player: Player
    projection: Projection | None

    @property
    def projected_points(self) -> float:
        if self.projection is None:
            return 0.0

        return self.projection.fantasy_points


@dataclass(frozen=True, slots=True)
class OptimizedLineup:
    starters: list[LineupSelection]
    bench: list[LineupSelection]

    @property
    def starter_projection(self) -> float:
        return sum(
            selection.projected_points
            for selection in self.starters
        )

    @property
    def bench_projection(self) -> float:
        return sum(
            selection.projected_points
            for selection in self.bench
        )


class LineupOptimizer:
    def __init__(
        self,
        projections: dict[str, Projection],
    ):
        self.projections = projections

    def projection_for(
        self,
        player: Player,
    ) -> Projection | None:
        return self.projections.get(
            normalize_name(player.name)
        )

    def projected_points(self, player: Player) -> float:
        projection = self.projection_for(player)

        if projection is None:
            return 0.0

        return projection.fantasy_points

    def players_at_position(
        self,
        team: Team,
        position: str,
    ) -> list[Player]:
        players = [
            player
            for player in team.players
            if base_position(player.position) == position
        ]

        return sorted(
            players,
            key=self.projected_points,
            reverse=True,
        )

    def create_selection(
        self,
        slot: str,
        player: Player,
    ) -> LineupSelection:
        return LineupSelection(
            slot=slot,
            player=player,
            projection=self.projection_for(player),
        )

    def optimize(self, team: Team) -> OptimizedLineup:
        starters: list[LineupSelection] = []
        selected_player_ids: set[int] = set()

        def select_player(
            slot: str,
            player: Player,
        ) -> None:
            starters.append(
                self.create_selection(slot, player)
            )
            selected_player_ids.add(id(player))

        quarterbacks = self.players_at_position(team, "QB")
        running_backs = self.players_at_position(team, "RB")
        wide_receivers = self.players_at_position(team, "WR")
        tight_ends = self.players_at_position(team, "TE")
        defenses = self.players_at_position(team, "DST")
        kickers = self.players_at_position(team, "K")

        if quarterbacks:
            select_player("QB", quarterbacks[0])

        for running_back in running_backs[:2]:
            select_player("RB", running_back)

        for wide_receiver in wide_receivers[:2]:
            select_player("WR", wide_receiver)

        if tight_ends:
            select_player("TE", tight_ends[0])

        flex_candidates = [
            player
            for player in team.players
            if (
                base_position(player.position)
                in {"RB", "WR", "TE"}
                and id(player) not in selected_player_ids
            )
        ]

        flex_candidates.sort(
            key=self.projected_points,
            reverse=True,
        )

        if flex_candidates:
            select_player("FLEX", flex_candidates[0])

        if defenses:
            select_player("DST", defenses[0])

        if kickers:
            select_player("K", kickers[0])

        bench_players = [
            player
            for player in team.players
            if id(player) not in selected_player_ids
        ]

        bench_players.sort(
            key=self.projected_points,
            reverse=True,
        )

        bench = [
            self.create_selection("BENCH", player)
            for player in bench_players
        ]

        return OptimizedLineup(
            starters=starters,
            bench=bench,
        )