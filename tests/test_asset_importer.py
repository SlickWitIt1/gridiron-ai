from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

IMPORTER_PATH = PROJECT_ROOT / "tools" / "import_player_assets.py"
spec = importlib.util.spec_from_file_location("import_player_assets", IMPORTER_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def player(name, position="WR", team="JAC"):
    return SimpleNamespace(name=name, position=position, team=team)


def record(name, position="WR", team="JAC"):
    first, *rest = name.split()
    return {
        "full_name": name,
        "first_name": first,
        "last_name": " ".join(rest),
        "position": position,
        "team": team,
    }


def assert_pass(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


# Exact name/team match.
sleeper = {"1": record("Brian Thomas Jr.")}
exact, suffix = module.build_indexes(sleeper)
match, match_type = module.choose_match(player("Brian Thomas Jr."), exact, suffix)
assert_pass("exact player match", match is not None and match[0] == "1")

# Suffix normalization can survive stale team data when the name+position is unique.
sleeper = {"2": record("Chris Rodriguez", position="RB", team="WAS")}
exact, suffix = module.build_indexes(sleeper)
match, match_type = module.choose_match(
    player("Chris Rodriguez Jr.", position="RB", team="JAC"),
    exact,
    suffix,
)
assert_pass("suffix match ignores stale team safely", match is not None and match[0] == "2")

# Alias support for known football names.
sleeper = {"3": record("Marquise Brown", position="WR", team="KC")}
exact, suffix = module.build_indexes(sleeper)
match, match_type = module.choose_match(
    player("Hollywood Brown", position="WR", team="PHI"),
    exact,
    suffix,
)
assert_pass("known alias match", match is not None and match[0] == "3")

# Multiple same-name/position candidates should remain unresolved rather than guess.
sleeper = {
    "4": record("Kyle Williams", position="WR", team="NE"),
    "5": record("Kyle Williams", position="WR", team="FA"),
}
exact, suffix = module.build_indexes(sleeper)
match, match_type = module.choose_match(
    player("Kyle Williams", position="WR", team="XXX"),
    exact,
    suffix,
)
assert_pass("ambiguous names remain unmatched", match is None)

print("\nALL ASSET IMPORTER TESTS PASSED")
