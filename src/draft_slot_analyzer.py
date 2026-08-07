import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from availability_engine import AvailabilityEngine
from monte_carlo import (
    MonteCarloResults,
    MonteCarloRunner,
)


def analyze_single_slot(
    arguments: tuple[int, int],
) -> MonteCarloResults:
    draft_slot, simulations_per_slot = arguments

    runner = MonteCarloRunner()

    return runner.run(
        draft_slot=draft_slot,
        simulations=simulations_per_slot,
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
    def best_slot(
        self,
    ) -> MonteCarloResults:
        return self.ranked_results[0]

    def result_for_slot(
        self,
        draft_slot: int,
    ) -> MonteCarloResults:
        for result in self.results:
            if result.draft_slot == draft_slot:
                return result

        raise ValueError(
            f"No results found for draft slot {draft_slot}."
        )

    def availability_for_slot(
        self,
        draft_slot: int,
    ) -> AvailabilityEngine:
        result = self.result_for_slot(draft_slot)

        availability = AvailabilityEngine()

        availability.merge_history(
            history=result.availability_history,
            simulations=result.simulations,
        )

        return availability


class DraftSlotAnalyzer:
    def analyze(
        self,
        simulations_per_slot: int = 100,
    ) -> DraftSlotAnalysis:
        cpu_count = os.cpu_count() or 4

        max_workers = min(
            8,
            cpu_count,
            10,
        )

        print(
            f"Using {max_workers} parallel "
            f"CPU workers.\n"
        )

        arguments = [
            (
                draft_slot,
                simulations_per_slot,
            )
            for draft_slot in range(1, 11)
        ]

        with ProcessPoolExecutor(
            max_workers=max_workers,
        ) as executor:
            results = list(
                executor.map(
                    analyze_single_slot,
                    arguments,
                )
            )

        results.sort(
            key=lambda result: result.draft_slot
        )

        return DraftSlotAnalysis(
            results=results
        )