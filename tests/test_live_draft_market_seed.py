from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from live_draft import LiveDraftSession


def main() -> None:
    live = LiveDraftSession(user_team_number=7, market_seed=0)
    mock_a = LiveDraftSession(user_team_number=7, market_seed=101)
    mock_b = LiveDraftSession(user_team_number=7, market_seed=202)

    assert live.user_team_number == 7
    assert mock_a.user_team_number == 7
    assert mock_b.user_team_number == 7
    assert live.current_pick == mock_a.current_pick == mock_b.current_pick == 1

    print("PASS  LiveDraftSession accepts explicit market seed")
    print("PASS  Live and Mock modes retain identical league/session structure")
    print()
    print("ALL MARKET-SEED TESTS PASSED")


if __name__ == "__main__":
    main()
