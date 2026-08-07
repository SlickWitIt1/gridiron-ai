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

    def available_count(
        self,
        player_name: str,
        overall_pick: int,
    ) -> int:
        """
        Count simulations where the player is available immediately
        before the specified overall pick.

        A player drafted at that pick or later counts as available.
        An undrafted player also counts as available.
        """
        if self.simulations == 0:
            return 0

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

        return drafted_at_or_after + undrafted_count

    def probability_available(
        self,
        player_name: str,
        overall_pick: int,
    ) -> float:
        if self.simulations == 0:
            return 0.0

        return (
            self.available_count(
                player_name=player_name,
                overall_pick=overall_pick,
            )
            / self.simulations
        )

    def survival_probability(
        self,
        player_name: str,
        current_pick: int,
        next_pick: int,
    ) -> float | None:
        """
        Probability that a player survives until next_pick,
        conditional on the player being available at current_pick.
        """
        if next_pick <= current_pick:
            raise ValueError(
                "Next pick must be later than current pick."
            )

        available_now = self.available_count(
            player_name=player_name,
            overall_pick=current_pick,
        )

        if available_now == 0:
            return None

        available_next = self.available_count(
            player_name=player_name,
            overall_pick=next_pick,
        )

        return available_next / available_now

    def average_pick(
        self,
        player_name: str,
    ) -> float | None:
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