from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from forecast_engine import ForecastEngine


def main() -> None:
    engine = ForecastEngine()
    forecast = engine.forecast(
        draft_slot=3,
        completed_player_names=(),
        current_pick=1,
        next_user_pick=3,
        simulations=10,
        player_names=(),
    )

    assert forecast.current_pick == 1
    assert forecast.next_user_pick == 3
    assert forecast.picks_between == 1
    assert len(forecast.pick_forecasts) == 1

    pick = forecast.pick(2)
    assert pick is not None
    assert pick.overall_pick == 2
    assert pick.team_number > 0
    assert pick.most_likely_position in {"QB", "RB", "WR", "TE"}
    assert 0.0 <= pick.probability <= 1.0

    probability_sum = sum(
        probability
        for _position, probability in pick.position_probabilities
    )
    assert 0.0 < probability_sum <= 1.000001

    print("PASS  exact-pick forecast generation")
    print("PASS  most-likely position + confidence")
    print("PASS  DraftForecast.pick lookup")
    print()
    print("ALL DRAFT TIMELINE TESTS PASSED")


if __name__ == "__main__":
    main()
