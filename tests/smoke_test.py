from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from draft_session_store import DraftSessionStore
from loader import load_players
from preferences import load_my_guys
from project_paths import validate_data_files
from projection_loader import load_projections
from strategy import DraftStrategy
from strategy_engine import StrategyEngine
from team import Team
from tier_engine import TierEngine


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise AssertionError(f"{name} failed{suffix}")
    print(f"PASS  {name}")


def main() -> None:
    print("Gridiron AI smoke test\n")

    validate_data_files()
    print("PASS  required data files")

    players = load_players()
    check("rankings load", len(players) > 100, f"loaded {len(players)}")

    my_guys = load_my_guys()
    check("My Guys load", len(my_guys) > 0, f"loaded {len(my_guys)}")

    projections = load_projections()
    check("projections load", len(projections) > 100, f"loaded {len(projections)}")

    tiers = TierEngine(projections).build_tiers()
    check("tier engine", len(tiers) > 100, f"built {len(tiers)} tiers")
    check(
        "tier metadata",
        all(info.tier_number >= 1 for info in tiers.values()),
    )

    empty_strategy = StrategyEngine().analyze(Team(7))
    check(
        "strategy engine",
        empty_strategy.primary_strategy == DraftStrategy.UNDETERMINED,
    )
    check(
        "strategy compatibility alias",
        empty_strategy.strategy == DraftStrategy.UNDETERMINED,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        save_path = Path(temp_dir) / "draft.json"
        store = DraftSessionStore(save_path)
        store.save(
            draft_slot=7,
            simulations=100,
            drafted_player_names=("Player One", "Player Two"),
        )
        loaded = store.load()
        check("draft save/load", loaded["draft_slot"] == 7)
        check(
            "draft history round-trip",
            loaded["drafted_player_names"] == ("Player One", "Player Two"),
        )

    print("\nALL CORE SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
