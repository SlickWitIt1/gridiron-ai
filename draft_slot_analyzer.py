from dataclasses import dataclass

from monte_carlo import (
    MonteCarloResults,
    MonteCarloRunner,
)


@dataclass(frozen=True, slots=True)
class DraftSlotAnalysis:
    results: list[MonteCarloResults]

    @property
    def ranked_results(
        self,
    ) -> list[MonteCarloResults]:
        return sorted(
            self.results,
            key=lambda result: (
                result.average_starter_projection,
                result.average_my_guys,
            ),
            reverse=True,
        )

    @property
    def best_slot(self) -> MonteCarloResults:
        return self.ranked_results[0]


class DraftSlotAnalyzer:
    def __init__(self):
        self.runner = MonteCarloRunner()

    def analyze(
        self,
        simulations_per_slot: int = 100,
    ) -> DraftSlotAnalysis:
        results: list[MonteCarloResults] = []

        for draft_slot in range(1, 11):
            print(
                f"Running slot {draft_slot} "
                f"({simulations_per_slot} simulations)..."
            )

            result = self.runner.run(
                draft_slot=draft_slot,
                simulations=simulations_per_slot,
            )

            results.append(result)

        return DraftSlotAnalysis(
            results=results
        )