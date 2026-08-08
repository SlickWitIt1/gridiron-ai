from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from coach_message_builder import CoachMessageBuilder


def fake(**overrides):
    values = dict(
        player_name="Puka Nacua",
        position="WR",
        confidence=89,
        score=86,
        survival_probability=0.08,
        position_run_probability=0.61,
        expected_position_picks=6.7,
        opportunity_cost=18.4,
        tier_number=1,
        players_remaining_in_tier=1,
        is_last_in_tier=True,
        is_my_guy=False,
        roster_need="GOOD FIT",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def explanation():
    return SimpleNamespace(
        reasons=(
            "Last available player in Tier 1.",
            "Only 8% chance he survives.",
            "Run pressure is elevated.",
            "Take-now path leads.",
        )
    )


def main() -> None:
    message = CoachMessageBuilder.build(fake(), explanation())

    assert "Puka Nacua" in message.command
    assert message.confidence_label == "Strong recommendation"
    assert "Tier 1" in message.summary
    assert "6.7" in message.summary
    assert "18.4" in message.summary
    assert len(message.key_points) <= 4

    patient = CoachMessageBuilder.build(
        fake(
            score=65,
            confidence=62,
            survival_probability=0.88,
            opportunity_cost=-7.0,
            is_last_in_tier=False,
            players_remaining_in_tier=5,
            expected_position_picks=1.0,
            position_run_probability=0.05,
            roster_need="NEUTRAL",
        ),
        explanation(),
    )
    assert "comfortable waiting" in patient.command
    assert patient.confidence_label == "Close decision"

    print("PASS  conversational recommendation summary")
    print("PASS  confidence language")
    print("PASS  aggressive/patient coaching tone")
    print("PASS  summary grounded only in engine facts")
    print()
    print("ALL COACH MESSAGE TESTS PASSED")


if __name__ == "__main__":
    main()
