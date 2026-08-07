from collections import Counter
from dataclasses import dataclass

from loader import load_players
from preferences import load_my_guys, normalize_name
from projection_loader import load_projections
from simulation import Simulation
from tier_engine import TierEngine


@dataclass(frozen=True, slots=True)
class WaitAnalysis:
    player_name: str
    simulations: int
    available_now_count: int
    survived_count: int

    likely_take_next_player: str | None = None
    likely_pass_current_player: str | None = None
    likely_pass_next_player: str | None = None

    take_path_projected_points: float = 0.0
    pass_path_projected_points: float = 0.0
    opportunity_cost: float = 0.0
    tier_disappearance_count: int = 0

    @property
    def available_now_probability(self) -> float:
        if self.simulations == 0:
            return 0.0
        return self.available_now_count / self.simulations

    @property
    def survival_probability(self) -> float | None:
        if self.available_now_count == 0:
            return None
        return self.survived_count / self.available_now_count

    @property
    def tier_disappearance_probability(self) -> float:
        if self.simulations == 0:
            return 0.0
        return self.tier_disappearance_count / self.simulations


class WaitAnalyzer:
    def __init__(self) -> None:
        self.players = load_players()
        self.approved_players = load_my_guys()
        self.projections = load_projections()
        self.tier_engine = TierEngine(self.projections)

        self.players_by_name = {
            normalize_name(player.name): player
            for player in self.players
        }

    @staticmethod
    def is_available(
        simulation: Simulation,
        player_name: str,
    ) -> bool:
        target = normalize_name(player_name)
        return any(
            normalize_name(player.name) == target
            for player in simulation.board.available_players
        )

    def _projected_points(self, player_name: str | None) -> float:
        if not player_name:
            return 0.0
        projection = self.projections.get(normalize_name(player_name))
        return projection.fantasy_points if projection is not None else 0.0

    @staticmethod
    def _most_common(counter: Counter[str]) -> str | None:
        if not counter:
            return None
        return counter.most_common(1)[0][0]

    @staticmethod
    def _user_pick_names(
        simulation: Simulation,
        draft_slot: int,
        current_pick: int,
        next_pick: int,
    ) -> tuple[str | None, str | None]:
        current_name = None
        next_name = None

        for draft_pick in simulation.engine.draft_results:
            if draft_pick.team_number != draft_slot:
                continue
            if draft_pick.overall == current_pick:
                current_name = draft_pick.player.name
            elif draft_pick.overall == next_pick:
                next_name = draft_pick.player.name

        return current_name, next_name

    def analyze_players(
        self,
        player_names: tuple[str, ...],
        draft_slot: int,
        current_pick: int,
        next_pick: int,
        simulations: int = 100,
    ) -> list[WaitAnalysis]:
        return self.analyze_live_players(
            player_names=player_names,
            draft_slot=draft_slot,
            completed_player_names=(),
            current_pick=current_pick,
            next_pick=next_pick,
            simulations=simulations,
        )

    def analyze_live_players(
        self,
        player_names: tuple[str, ...],
        draft_slot: int,
        completed_player_names: tuple[str, ...],
        current_pick: int,
        next_pick: int,
        simulations: int = 100,
    ) -> list[WaitAnalysis]:
        if next_pick <= current_pick:
            raise ValueError("Next pick must be later than current pick.")

        if current_pick != len(completed_player_names) + 1:
            raise ValueError(
                "Current pick does not match the number "
                "of completed live draft picks."
            )

        completed_normalized = {
            normalize_name(player_name)
            for player_name in completed_player_names
        }

        live_available_names = tuple(
            player.name
            for player in self.players
            if normalize_name(player.name) not in completed_normalized
        )
        live_tiers = self.tier_engine.build_tiers(
            available_names=live_available_names
        )

        results: list[WaitAnalysis] = []

        for player_name in player_names:
            normalized_candidate = normalize_name(player_name)

            if normalized_candidate in completed_normalized:
                results.append(
                    WaitAnalysis(
                        player_name=player_name,
                        simulations=simulations,
                        available_now_count=0,
                        survived_count=0,
                    )
                )
                continue

            candidate_tier = live_tiers.get(normalized_candidate)
            tier_member_names: set[str] = set()

            if candidate_tier is not None:
                tier_member_names = {
                    normalized_name
                    for normalized_name, tier_info in live_tiers.items()
                    if (
                        tier_info.position == candidate_tier.position
                        and tier_info.tier_number == candidate_tier.tier_number
                    )
                }

            survived_count = 0
            tier_disappearance_count = 0
            take_next_counter: Counter[str] = Counter()
            pass_current_counter: Counter[str] = Counter()
            pass_next_counter: Counter[str] = Counter()
            take_value_total = 0.0
            pass_value_total = 0.0

            for seed in range(simulations):
                # TAKE PATH: lock the candidate into the current live pick,
                # then simulate forward through the user's next selection.
                take_simulation = Simulation(
                    user_team_number=draft_slot,
                    seed=seed,
                    players=self.players,
                    approved_players=self.approved_players,
                    initial_player_names=(
                        completed_player_names + (player_name,)
                    ),
                )
                take_simulation.run(
                    print_picks=False,
                    max_overall_pick=next_pick,
                )
                _, take_next_name = self._user_pick_names(
                    simulation=take_simulation,
                    draft_slot=draft_slot,
                    current_pick=current_pick,
                    next_pick=next_pick,
                )
                if take_next_name:
                    take_next_counter[take_next_name] += 1

                take_value_total += (
                    self._projected_points(player_name)
                    + self._projected_points(take_next_name)
                )

                # PASS PATH: forbid the candidate at the current pick. Stop
                # immediately before the next user pick so we can measure
                # survival and whether the candidate's whole tier vanished.
                pass_simulation = Simulation(
                    user_team_number=draft_slot,
                    seed=seed,
                    players=self.players,
                    approved_players=self.approved_players,
                    forbidden_players_by_pick={
                        current_pick: {player_name},
                    },
                    initial_player_names=completed_player_names,
                )
                pass_simulation.run(
                    print_picks=False,
                    max_overall_pick=next_pick - 1,
                )

                if self.is_available(pass_simulation, player_name):
                    survived_count += 1

                if tier_member_names:
                    available_at_next_pick = {
                        normalize_name(player.name)
                        for player in pass_simulation.board.available_players
                    }
                    if not (tier_member_names & available_at_next_pick):
                        tier_disappearance_count += 1

                # Continue the same simulated draft through the next user pick.
                pass_simulation.run(
                    print_picks=False,
                    max_overall_pick=next_pick,
                )
                pass_current_name, pass_next_name = self._user_pick_names(
                    simulation=pass_simulation,
                    draft_slot=draft_slot,
                    current_pick=current_pick,
                    next_pick=next_pick,
                )
                if pass_current_name:
                    pass_current_counter[pass_current_name] += 1
                if pass_next_name:
                    pass_next_counter[pass_next_name] += 1

                pass_value_total += (
                    self._projected_points(pass_current_name)
                    + self._projected_points(pass_next_name)
                )

            take_path_value = take_value_total / simulations
            pass_path_value = pass_value_total / simulations

            results.append(
                WaitAnalysis(
                    player_name=player_name,
                    simulations=simulations,
                    available_now_count=simulations,
                    survived_count=survived_count,
                    likely_take_next_player=self._most_common(
                        take_next_counter
                    ),
                    likely_pass_current_player=self._most_common(
                        pass_current_counter
                    ),
                    likely_pass_next_player=self._most_common(
                        pass_next_counter
                    ),
                    take_path_projected_points=take_path_value,
                    pass_path_projected_points=pass_path_value,
                    opportunity_cost=(
                        take_path_value - pass_path_value
                    ),
                    tier_disappearance_count=tier_disappearance_count,
                )
            )

        return results
