from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from forecast_engine import ForecastEngine
from live_draft import LiveDraftSession


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise AssertionError(f"{name} failed{suffix}")
    print(f"PASS  {name}")


def run_forecast(simulations: int = 12):
    session = LiveDraftSession(user_team_number=7)
    return ForecastEngine(players=session.players).forecast(
        draft_slot=session.user_team_number,
        completed_player_names=session.completed_player_names,
        current_pick=session.current_pick,
        next_user_pick=session.next_user_pick,
        simulations=simulations,
        player_names=tuple(player.name for player in session.available_players(3)),
    )


def main() -> None:
    forecast = run_forecast()

    check("next pick found", forecast.next_user_pick > forecast.current_pick)
    check(
        "picks between",
        forecast.picks_between == forecast.next_user_pick - forecast.current_pick - 1,
    )
    check("four position forecasts", len(forecast.position_forecasts) == 4)
    check(
        "expected picks bounded",
        all(
            0.0 <= item.expected_picks <= forecast.picks_between
            for item in forecast.position_forecasts
        ),
    )
    check(
        "probabilities bounded",
        all(
            0.0 <= item.probability_selected <= 1.0
            and 0.0 <= item.run_probability <= 1.0
            for item in forecast.position_forecasts
        ),
    )
    check("requested players returned", len(forecast.player_forecasts) == 3)
    check(
        "player survival bounded",
        all(0.0 <= item.survival_probability <= 1.0 for item in forecast.player_forecasts),
    )
    check("tier forecasts created", len(forecast.tier_forecasts) > 0)
    check(
        "tier probabilities complementary",
        all(
            abs(
                item.survival_probability
                + item.disappearance_probability
                - 1.0
            ) < 1e-9
            for item in forecast.tier_forecasts
        ),
    )

    repeated = run_forecast()
    check("deterministic seeded forecast", forecast == repeated)

    print("\nALL FORECAST ENGINE TESTS PASSED")


if __name__ == "__main__":
    main()
