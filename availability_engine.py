from collections import defaultdict
from collections.abc import Iterable

from draft_pick import DraftPick
from preferences import normalize_name


class AvailabilityEngine:
    def __init__(self) -> None:
        self.history: dict[str, list[int]] = defaultdict(list)
        self.simulations = 0

    def record_draft(
        self,
        draft_results: Iterable[DraftPick],
    ) -> None:
        """
        Record where each drafted player was selected in one simulation.

        Players who are not drafted are treated as still available after
        the draft when availability probabilities are calculated.
        """
        self.simulations += 1

        for draft_pick in draft_results:
            key = normalize_name(
                draft_pick.player.name
            )

            self.history[key].append(
                draft_pick.overall
            )

    def merge_history(
        self,
        history: dict[str, tuple[int, ...]],
        simulations: int,
    ) -> None:
        """
        Merge availability data produced by another process.
        """
        self.simulations += simulations

        for player_name, picks in history.items():
            self.history[player_name].extend(picks)

    def export_history(
        self,
    ) -> dict[str, tuple[int, ...]]:
        return {
            player_name: tuple(picks)
            for player_name, picks in self.history.items()
        }

    def probability_available(
        self,
        player_name: str,
        overall_pick: int,
    ) -> float:
        """
        Return the probability that a player is still available before
        the specified overall pick.

        A player drafted at that pick or later counts as available.
        A player who went undrafted also counts as available.
        """
        if self.simulations == 0:
            return 0.0

        key = normalize_name(player_name)
        drafted_picks = self.history.get(key, [])

        drafted_at_or_after = sum(
            1
            for pick in drafted_picks
            if pick >= overall_pick
        )

        undrafted_count = (
            self.simulations - len(drafted_picks)
        )

        available_count = (
            drafted_at_or_after
            + undrafted_count
        )

        return available_count / self.simulations

    def average_pick(
        self,
        player_name: str,
    ) -> float | None:
        """
        Average selection number in simulations where the player
        was drafted.
        """
        key = normalize_name(player_name)
        picks = self.history.get(key, [])

        if not picks:
            return None

        return sum(picks) / len(picks)

    def draft_rate(
        self,
        player_name: str,
    ) -> float:
        if self.simulations == 0:
            return 0.0

        key = normalize_name(player_name)
        picks = self.history.get(key, [])

        return len(picks) / self.simulations