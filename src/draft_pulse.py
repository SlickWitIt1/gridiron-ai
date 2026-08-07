from collections import Counter
from dataclasses import dataclass

from team import base_position


TRACKED_POSITIONS = ("RB", "WR", "QB", "TE")


@dataclass(frozen=True, slots=True)
class DraftPulseSnapshot:
    window_size: int
    completed_picks: int
    position_counts: dict[str, int]
    run_position: str | None
    run_count: int
    run_strength: str
    headline: str
    detail: str

    def count(self, position: str) -> int:
        return self.position_counts.get(position, 0)


class DraftPulseAnalyzer:
    def __init__(self, window_size: int = 10) -> None:
        if window_size < 4:
            raise ValueError("Draft pulse window must be at least four picks.")

        self.window_size = window_size

    def analyze(self, draft_results) -> DraftPulseSnapshot:
        recent_picks = list(draft_results)[-self.window_size :]

        positions = [
            base_position(draft_pick.player.position)
            for draft_pick in recent_picks
        ]

        counts = Counter(
            position
            for position in positions
            if position in TRACKED_POSITIONS
        )

        position_counts = {
            position: counts.get(position, 0)
            for position in TRACKED_POSITIONS
        }

        completed_picks = len(recent_picks)

        if completed_picks < 4 or not counts:
            return DraftPulseSnapshot(
                window_size=self.window_size,
                completed_picks=completed_picks,
                position_counts=position_counts,
                run_position=None,
                run_count=0,
                run_strength="NONE",
                headline="Draft settling in",
                detail=(
                    "Record a few more picks to detect positional runs."
                    if completed_picks < 4
                    else "No meaningful positional run detected."
                ),
            )

        run_position, run_count = counts.most_common(1)[0]
        share = run_count / completed_picks

        if run_count >= 7 and share >= 0.60:
            run_strength = "STRONG"
            headline = f"{run_position} run detected"
        elif run_count >= 5 and share >= 0.50:
            run_strength = "ACTIVE"
            headline = f"{run_position} run forming"
        elif run_count >= 4 and share >= 0.40:
            run_strength = "WATCH"
            headline = f"Watch the {run_position} market"
        else:
            run_strength = "NONE"
            headline = "Balanced draft flow"

        if run_strength == "NONE":
            detail = (
                f"No position controls the last {completed_picks} picks."
            )
            run_position = None
            run_count = 0
        else:
            detail = (
                f"{run_count} of the last {completed_picks} selections "
                f"were {run_position}s."
            )

        return DraftPulseSnapshot(
            window_size=self.window_size,
            completed_picks=completed_picks,
            position_counts=position_counts,
            run_position=run_position,
            run_count=run_count,
            run_strength=run_strength,
            headline=headline,
            detail=detail,
        )
