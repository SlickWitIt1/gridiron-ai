from dataclasses import dataclass

from config import USER_TEAM_NUMBER
from lineup_optimizer import LineupOptimizer
from projection_loader import load_projections
from simulation import Simulation


@dataclass
class MonteCarloResults:
    simulations: int
    average_projection: float
    best_projection: float
    worst_projection: float


class MonteCarloRunner:

    def __init__(self):

        self.projections = load_projections()

    def run(
        self,
        simulations: int = 100,
    ) -> MonteCarloResults:

        totals = []

        optimizer = LineupOptimizer(self.projections)

        for seed in range(simulations):

            simulation = Simulation(
                user_team_number=USER_TEAM_NUMBER,
                seed=seed,
            )

            simulation.run(print_picks=False)

            team = simulation.league.teams[
                USER_TEAM_NUMBER - 1
            ]

            lineup = optimizer.optimize(team)

            totals.append(
                lineup.starter_projection
            )

        return MonteCarloResults(
            simulations=simulations,
            average_projection=sum(totals) / len(totals),
            best_projection=max(totals),
            worst_projection=min(totals),
        )