from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from wait_intelligence import CostOfWaitingBuilder


def rec(**overrides):
    values = dict(
        player_name="Player A",
        survival_probability=0.14,
        tier_disappearance_probability=0.82,
        opportunity_cost=11.3,
        take_path_projected_points=331.4,
        pass_path_projected_points=320.1,
        likely_take_next_player="Player B",
        likely_pass_current_player="Player C",
        likely_pass_next_player="Player D",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def main() -> None:
    high = CostOfWaitingBuilder.build(
        rec(),
        current_pick=63,
        next_pick=78,
    )
    assert high.headline == "EXPENSIVE TO WAIT"
    assert high.risk_level == "high"
    assert high.pick_window == "PICK 63 → 78  •  14 selections in between"
    assert high.survival_text == "14%"
    assert high.tier_risk_text == "82%"
    assert high.point_swing_text == "+11.3"
    assert "Player A + Player B" in high.take_path_text
    assert "Player C + Player D" in high.pass_path_text

    safe = CostOfWaitingBuilder.build(
        rec(
            survival_probability=0.84,
            tier_disappearance_probability=0.15,
            opportunity_cost=-5.2,
        ),
        current_pick=63,
        next_pick=78,
    )
    assert safe.headline == "WAIT PATH LEADS"
    assert safe.risk_level == "safe"
    assert safe.point_swing_text == "-5.2"

    final_pick = CostOfWaitingBuilder.build(
        rec(survival_probability=None),
        current_pick=153,
        next_pick=None,
    )
    assert "FINAL USER PICK" in final_pick.pick_window
    assert final_pick.survival_text == "N/A"

    print("PASS  high wait-risk classification")
    print("PASS  safe-to-wait classification")
    print("PASS  take/pass path formatting")
    print("PASS  current-to-next-pick window")
    print()
    print("ALL COST OF WAITING TESTS PASSED")


if __name__ == "__main__":
    main()
