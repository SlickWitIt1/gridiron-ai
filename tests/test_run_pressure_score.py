from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from loader import load_players
from recommendation_engine import RecommendationEngine


def main() -> None:
    engine = RecommendationEngine(load_players())

    high = SimpleNamespace(
        picks_between=14,
        position=lambda position: SimpleNamespace(
            expected_picks=7.0,
            run_probability=0.60,
        ),
    )
    low = SimpleNamespace(
        picks_between=14,
        position=lambda position: SimpleNamespace(
            expected_picks=1.0,
            run_probability=0.05,
        ),
    )

    high_score, high_expected, high_prob = engine._run_pressure(
        forecast=high,
        position="WR",
    )
    low_score, _, _ = engine._run_pressure(
        forecast=low,
        position="WR",
    )

    assert high_score > low_score
    assert high_expected == 7.0
    assert high_prob == 0.60
    assert 0.0 <= high_score <= engine.RUN_PRESSURE_MAX

    print("PASS  position-run pressure enters recommendation score")
    print("PASS  run pressure bounded by component maximum")
    print()
    print("ALL RUN-PRESSURE TESTS PASSED")


if __name__ == "__main__":
    main()
