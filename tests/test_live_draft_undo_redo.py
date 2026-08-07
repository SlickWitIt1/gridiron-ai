from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from live_draft import LiveDraftSession


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    session = LiveDraftSession(user_team_number=3)
    first = session.available_players(limit=3)

    session.record_pick(first[0].name)
    session.record_pick(first[1].name)
    session.record_pick(first[2].name)

    require(session.current_pick == 4, "Expected pick 4 after three selections.")

    undone_3 = session.undo_last_pick()
    undone_2 = session.undo_last_pick()

    require(session.can_redo, "Redo should be available after undo.")
    require(session.current_pick == 2, "Expected to be back at pick 2.")

    redone_2 = session.redo_last_pick()
    require(redone_2.player.name == undone_2.player.name, "Redo order is wrong.")
    require(session.current_pick == 3, "Expected pick 3 after first redo.")
    require(session.can_redo, "Second redo should still be available.")

    redone_3 = session.redo_last_pick()
    require(redone_3.player.name == undone_3.player.name, "Second redo is wrong.")
    require(session.current_pick == 4, "Expected pick 4 after both redos.")
    require(not session.can_redo, "Redo stack should now be empty.")

    # A new branch after undo must invalidate redo history.
    session.undo_last_pick()
    require(session.can_redo, "Redo should be available before branching.")
    replacement = next(
        player
        for player in session.available_players()
        if player.name != undone_3.player.name
    )
    session.record_pick(replacement.name)
    require(not session.can_redo, "New selection should clear redo history.")

    print("PASS  in-place undo/redo")
    print("PASS  redo order")
    print("PASS  new pick clears redo history")
    print()
    print("ALL UNDO/REDO TESTS PASSED")


if __name__ == "__main__":
    main()
