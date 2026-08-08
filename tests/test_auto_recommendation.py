from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from auto_recommendation import AutoRecommendationCandidateBuilder
from live_draft import LiveDraftSession
from preferences import normalize_name


def main() -> None:
    session = LiveDraftSession(user_team_number=1)
    available = session.available_players()
    my_guy_name = available[7].name

    builder = AutoRecommendationCandidateBuilder(
        approved_players={normalize_name(my_guy_name)}
    )
    pool = builder.build(session)

    assert pool.scanned_players == len(available)
    assert pool.legal_players > 0
    assert 1 <= len(pool.player_names) <= builder.MAX_CANDIDATES
    assert available[0].name in pool.player_names
    assert my_guy_name in pool.player_names
    assert len(pool.player_names) == len(set(pool.player_names))

    print("PASS  full-board scan")
    print("PASS  capped deep-analysis shortlist")
    print("PASS  BPA survives screening")
    print("PASS  My Guy receives shortlist consideration")
    print()
    print("ALL AUTO-RECOMMENDATION CANDIDATE TESTS PASSED")


if __name__ == "__main__":
    main()
