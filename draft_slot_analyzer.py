import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

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
    def best_slot(self) -> MonteCarloResults:
        return self.ranked_results[0]


class DraftSlotAnalyzer:
    def analyze(
        self,
        simulations_per_slot: int = 100,
    ) -> DraftSlotAnalysis:
        cpu_count = os.cpu_count() or 4

        # Leave some breathing room for macOS and VS Code.
        max_workers = min(
            8,
            cpu_count,
            10,
        )

        print(
            f"Using {max_workers} parallel CPU workers.\n"
        )

        arguments = [
            (draft_slot, simulations_per_slot)
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

        # Process results in normal slot order before ranking.
        results.sort(
            key=lambda result: result.draft_slot
        )

        return DraftSlotAnalysis(
            results=results
        )