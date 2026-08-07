from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from asset_manager import AssetManager, asset_filename, normalized_asset_name, short_player_name


def check(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")
    print(f"PASS  {name}")


def main() -> None:
    check("Jahmyr Gibbs abbreviation", short_player_name("Jahmyr Gibbs"), "J. Gibbs")
    check("Ja'Marr Chase abbreviation", short_player_name("Ja'Marr Chase"), "J. Chase")
    check("Amon-Ra surname preserved", short_player_name("Amon-Ra St. Brown"), "A. St. Brown")
    check("suffix preserved", short_player_name("Kenneth Walker III"), "K. Walker III")
    check("asset normalization", normalized_asset_name("Ja'Marr Chase"), "jamarrchase")
    check("asset filename", asset_filename("Amon-Ra St. Brown"), "amon_ra_st_brown")

    with tempfile.TemporaryDirectory() as temp_dir:
        manifest = Path(temp_dir) / "player_assets.json"
        manifest.write_text('{"version": 1, "players": {}}', encoding="utf-8")
        manager = AssetManager(manifest)
        check("missing headshot safe", manager.headshot("No Player"), None)

    print("\nALL ASSET MANAGER TESTS PASSED")


if __name__ == "__main__":
    main()
