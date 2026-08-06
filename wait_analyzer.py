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
    def is_available(
        simulation: Simulation,
        player_name: str,
    ) -> bool:
        target = normalize_name(player_name)

        return any(
            normalize_name(player.name) == target
            for player in simulation.board.available_players
        )

    def analyze_players(
        self,
        player_names: tuple[str, ...],
        draft_slot: int,
        current_pick: int,
        next_pick: int,
        simulations: int = 100,
    ) -> list[WaitAnalysis]:
        if next_pick <= current_pick:
            raise ValueError(
                "Next pick must be later than current pick."
            )

        available_counts = {
            player_name: 0
            for player_name in player_names
        }

        survived_counts = {
            player_name: 0
            for player_name in player_names
        }

        for seed in range(simulations):
            # Stop immediately before the user's current pick.
            baseline = Simulation(
                user_team_number=draft_slot,
                seed=seed,
                players=self.players,
                approved_players=self.approved_players,
            )

            baseline.run(
                print_picks=False,
                max_overall_pick=current_pick - 1,
            )

            available_players = [
                player_name
                for player_name in player_names
                if self.is_available(
                    baseline,
                    player_name,
                )
            ]

            for player_name in available_players:
                available_counts[player_name] += 1

                # Force the user's team to pass at current_pick.
                # Stop immediately before next_pick.
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

                counterfactual.run(
                    print_picks=False,
                    max_overall_pick=next_pick - 1,
                )

                if self.is_available(
                    counterfactual,
                    player_name,
                ):
                    survived_counts[player_name] += 1

        return [
            WaitAnalysis(
                player_name=player_name,
                simulations=simulations,
                available_now_count=(
                    available_counts[player_name]
                ),
                survived_count=(
                    survived_counts[player_name]
                ),
            )
            for player_name in player_names
        ]