from dataclasses import dataclass

from lineup_optimizer import LineupOptimizer
from loader import load_players
from preferences import load_my_guys, normalize_name
from projection_loader import load_projections
from simulation import Simulation


@dataclass(frozen=True, slots=True)
class MonteCarloResults:
    draft_slot: int
    simulations: int

    average_starter_projection: float
    best_starter_projection: float
    worst_starter_projection: float

    average_roster_projection: float
    average_my_guys: float
    average_roster_rank: float
    average_surplus: float


class MonteCarloRunner:
    def __init__(self):
        self.players = load_players()
        self.approved_players = load_my_guys()
        self.projections = load_projections()

        self.optimizer = LineupOptimizer(
            self.projections
        )

    def run(
        self,
        draft_slot: int,
        simulations: int = 100,
    ) -> MonteCarloResults:
        if not 1 <= draft_slot <= 10:
            raise ValueError(
                "Draft slot must be between 1 and 10."
            )

        if simulations < 1:
            raise ValueError(
                "Simulations must be at least 1."
            )

        starter_totals: list[float] = []
        roster_totals: list[float] = []
        my_guys_totals: list[int] = []
        roster_rank_totals: list[float] = []
        surplus_totals: list[float] = []

        for seed in range(simulations):
            simulation = Simulation(
                user_team_number=draft_slot,
                seed=seed,
                players=self.players,
                approved_players=self.approved_players,
            )

            engine = simulation.run(
                print_picks=False
            )

            team = simulation.league.teams[
                draft_slot - 1
            ]

            lineup = self.optimizer.optimize(team)

            roster_projection = (
                lineup.starter_projection
                + lineup.bench_projection
            )

            my_guys_count = sum(
                1
                for player in team.players
                if normalize_name(player.name)
                in self.approved_players
            )

            average_roster_rank = (
                sum(
                    player.rank
                    for player in team.players
                )
                / len(team.players)
            )

            user_picks = [
                draft_pick
                for draft_pick in engine.draft_results
                if draft_pick.team_number == draft_slot
            ]

            total_surplus = sum(
                draft_pick.overall
                - draft_pick.player.rank
                for draft_pick in user_picks
            )

            starter_totals.append(
                lineup.starter_projection
            )

            roster_totals.append(
                roster_projection
            )

            my_guys_totals.append(
                my_guys_count
            )

            roster_rank_totals.append(
                average_roster_rank
            )

            surplus_totals.append(
                total_surplus
            )

        return MonteCarloResults(
            draft_slot=draft_slot,
            simulations=simulations,
            average_starter_projection=(
                sum(starter_totals)
                / len(starter_totals)
            ),
            best_starter_projection=max(
                starter_totals
            ),
            worst_starter_projection=min(
                starter_totals
            ),
            average_roster_projection=(
                sum(roster_totals)
                / len(roster_totals)
            ),
            average_my_guys=(
                sum(my_guys_totals)
                / len(my_guys_totals)
            ),
            average_roster_rank=(
                sum(roster_rank_totals)
                / len(roster_rank_totals)
            ),
            average_surplus=(
                sum(surplus_totals)
                / len(surplus_totals)
            ),
        )