from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from coach import CoachMessageType, CoachSeverity
from coach_engine import CoachEngine


class Strategy(Enum):
    HERO_RB = "Hero RB"
    ROBUST_RB = "Robust RB"


def recommendation(**overrides):
    values = {
        "player_name": "Alpha WR",
        "position": "WR",
        "tier_number": 1,
        "players_remaining_in_tier": 1,
        "is_last_in_tier": True,
        "survival_probability": 0.08,
        "strategy_fit_label": "EXCELLENT",
        "strategy_fit_explanation": "Excellent fit.",
        "primary_strategy": "Hero RB",
        "opportunity_cost": 11.2,
        "tier_disappearance_probability": 0.82,
        "action": "DRAFT NOW",
        "reasons": (),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def forecast(**overrides):
    values = {
        "most_likely_run": "WR",
        "run_probability": 0.78,
        "player_forecasts": (
            SimpleNamespace(player_name="Alpha WR", survival_probability=0.08),
        ),
        "tier_forecasts": (
            SimpleNamespace(
                position="WR",
                tier_number=1,
                disappearance_probability=0.82,
            ),
        ),
    }
    values.update(overrides)
    result = SimpleNamespace(**values)
    result.player = lambda name: next(
        (
            item
            for item in result.player_forecasts
            if item.player_name.casefold() == name.casefold()
        ),
        None,
    )
    return result


def strategy(value):
    return SimpleNamespace(primary_strategy=value)


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS  {name}")


def main() -> None:
    engine = CoachEngine()

    empty = engine.recommendation_message(())
    check("empty recommendation message", empty.message_type == CoachMessageType.UPDATE)

    message = engine.recommendation_message(
        (recommendation(),),
        forecast=forecast(),
        strategy_result=strategy(Strategy.HERO_RB),
    )
    check("recommendation type", message.message_type == CoachMessageType.RECOMMENDATION)
    check("recommendation player", message.recommended_player == "Alpha WR")
    check("recommendation summary", message.summary == "Draft Alpha WR.")
    check("recommendation bullet limit", len(message.bullets) <= 4)
    check("survival context", any("8%" in bullet for bullet in message.bullets))
    check("opportunity context", any("11.2" in bullet for bullet in message.bullets))

    followed = engine.selection_message(
        selected_player_name="Alpha WR",
        previous_recommendation=recommendation(),
        previous_strategy=strategy(Strategy.HERO_RB),
        current_strategy=strategy(Strategy.HERO_RB),
    )
    check("followed detected", followed.message_type == CoachMessageType.FOLLOWED)
    check("followed positive", followed.severity == CoachSeverity.POSITIVE)

    deviation = engine.selection_message(
        selected_player_name="Second RB",
        previous_recommendation=recommendation(),
        previous_strategy=strategy(Strategy.HERO_RB),
        current_strategy=strategy(Strategy.ROBUST_RB),
        previous_forecast=forecast(),
        current_forecast=forecast(most_likely_run="RB", run_probability=0.66),
    )
    check("deviation detected", deviation.message_type == CoachMessageType.DEVIATION)
    check("deviation warning", deviation.severity == CoachSeverity.WARNING)
    check("strategy shift explained", any("shifted" in bullet for bullet in deviation.bullets))
    check("tier risk explained", any("82%" in bullet for bullet in deviation.bullets))
    check("forecast update explained", any("66%" in bullet for bullet in deviation.bullets))

    print("\nALL COACH ENGINE TESTS PASSED")


if __name__ == "__main__":
    main()
