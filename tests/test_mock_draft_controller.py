from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from draft_mode import MockDraftController
from live_draft import LiveDraftSession


def main() -> None:
    session = LiveDraftSession(
        user_team_number=3,
        market_seed=12345,
    )
    controller = MockDraftController(
        session,
        delay_ms=0,
    )

    assert session.current_pick == 1
    assert not session.is_user_turn

    first = controller.draft_next_ai_pick()
    second = controller.draft_next_ai_pick()

    assert first is not None
    assert second is not None
    assert first.overall == 1
    assert second.overall == 2
    assert first.team_number == 1
    assert second.team_number == 2

    assert session.current_pick == 3
    assert session.is_user_turn

    # The mock controller and Live mode both feed the same session API.
    user_pick = session.record_pick(session.available_players()[0].name)
    assert user_pick.overall == 3
    assert user_pick.team_number == 3

    next_ai = controller.draft_next_ai_pick()
    assert next_ai is not None
    assert next_ai.overall == 4
    assert next_ai.team_number == 4

    print("PASS  AI opponents use shared LiveDraftSession")
    print("PASS  controller stops naturally at user slot")
    print("PASS  user pick and AI picks share one draft history")
    print("PASS  snake order remains owned by the existing League/session")
    print()
    print("ALL MOCK DRAFT CONTROLLER TESTS PASSED")


if __name__ == "__main__":
    main()
