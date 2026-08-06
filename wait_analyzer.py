from dataclasses import dataclass

from loader import load_players
from preferences import (
    load_my_guys,
    normalize_name,
)
from simulation import Simulation


@dataclass(frozen=True, slots=True)
class WaitAnalysis:
    player_name: str
    simulations: int
    available_now_count: int
    survived_count: int

    @property
    def available_now_probability(self) -> float:
        if self.simulations == 0:
            return 0.0

        return (
            self.available_now_count
            / self.simulations
        )

    @property
    def survival_probability(self) -> float | None:
        if self.available_now_count == 0:
            return None

        return (
            self.survived_count
            / self.available_now_count
        )


class WaitAnalyzer:
    def __init__(self) -> None:
        self.players = load_players()
        self.approved_players = load_my_guys()

    @staticmethod
    def player_pick(
        engine,
        player_name: str,
    ) -> int | None:
        target = normalize_name(player_name)

        for draft_pick in engine.draft_results:
            if (
                normalize_name(
                    draft_pick.player.name
                )
                == target
            ):
                return draft_pick.overall

        return None

    def analyze(
        self,
        player_name: str,
        draft_slot: int,
        current_pick: int,
        next_pick: int,
        simulations: int = 100,
    ) -> WaitAnalysis:
        available_now_count = 0
        survived_count = 0

        for seed in range(simulations):
            baseline = Simulation(
                user_team_number=draft_slot,
                seed=seed,
                players=self.players,
                approved_players=self.approved_players,
            )

            baseline_engine = baseline.run(
                print_picks=False
            )

            baseline_pick = self.player_pick(
                baseline_engine,
                player_name,
            )

            is_available_now = (
                baseline_pick is None
                or baseline_pick >= current_pick
            )

            if not is_available_now:
                continue

            available_now_count += 1

            counterfactual = Simulation(
                user_team_number=draft_slot,
                seed=seed,
                players=self.players,
                approved_players=self.approved_players,
                forbidden_players_by_pick={
                    current_pick: {
                        player_name,
                    }
                },
            )

            counterfactual_engine = (
                counterfactual.run(
                    print_picks=False
                )
            )

            counterfactual_pick = self.player_pick(
                counterfactual_engine,
                player_name,
            )

            survived = (
                counterfactual_pick is None
                or counterfactual_pick >= next_pick
            )

            if survived:
                survived_count += 1

        return WaitAnalysis(
            player_name=player_name,
            simulations=simulations,
            available_now_count=available_now_count,
            survived_count=survived_count,
        )