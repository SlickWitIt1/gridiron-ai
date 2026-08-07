from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from live_draft import LiveDraftSession


def test_undo_restores_player_without_rebuilding_session():
    session = LiveDraftSession(user_team_number=7)
    original_id = id(session)
    first = session.available_players()[0]

    pick = session.record_pick(first.name)
    assert not session.is_player_available(first.name)
    assert session.current_pick == 2

    removed = session.undo_last_pick()

    assert id(session) == original_id
    assert removed.player.name == pick.player.name
    assert session.is_player_available(first.name)
    assert session.current_pick == 1
    assert not session.draft_results


def test_undo_removes_player_from_correct_team_roster():
    session = LiveDraftSession(user_team_number=7)
    first = session.available_players()[0]
    pick = session.record_pick(first.name)
    team = session.league.teams[pick.team_number - 1]
    assert any(player.name == first.name for player in team.players)

    session.undo_last_pick()
    assert all(player.name != first.name for player in team.players)
