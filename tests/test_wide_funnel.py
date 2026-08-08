from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from auto_recommendation import AutoRecommendationCandidateBuilder
from live_draft import LiveDraftSession
from team import base_position


def main() -> None:
    session = LiveDraftSession(user_team_number=3)
    builder = AutoRecommendationCandidateBuilder()
    pool = builder.build(session)

    assert builder.MAX_CANDIDATES == 20
    assert 10 < len(pool.player_names) <= 20
    assert pool.scanned_players == len(session.available_players())
    assert len(pool.player_names) == len(set(pool.player_names))

    # Player.position values in this project are things like RB1 / WR3 / QB2,
    # so normalize them with the same base_position() helper the app uses.
    by_name = {
        player.name: player
        for player in session.available_players()
    }
    positions = {
        base_position(by_name[name].position)
        for name in pool.player_names
        if name in by_name
    }

    assert len(
        positions.intersection({"QB", "RB", "WR", "TE"})
    ) >= 3

    print(f"Shortlist size: {len(pool.player_names)}")
    print(f"Positions represented: {sorted(positions)}")
    print("PASS  full-board scan")
    print("PASS  broad shortlist expands beyond old top-10 cap")
    print("PASS  shortlist preserves positional diversity")
    print()
    print("ALL WIDE-FUNNEL TESTS PASSED")


if __name__ == "__main__":
    main()
