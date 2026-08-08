from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from recommendation_explanation import RecommendationExplanationBuilder


def fake(**overrides):
    values = dict(
        player_name="Test Player",
        position="WR",
        score=93.0,
        grade="A+",
        action="DRAFT NOW",
        confidence=91,
        survival_probability=0.14,
        tier_number=4,
        players_remaining_in_tier=1,
        is_last_in_tier=True,
        tier_drop_points=18.0,
        tier_disappearance_probability=0.88,
        opportunity_cost=12.4,
        projection_advantage=16.0,
        roster_fit_score=9.0,
        roster_need="WR2 starter",
        strategy_fit_label="Strong",
        primary_strategy="Balanced",
        is_my_guy=False,
        reasons=("Engine reason.",),
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def main() -> None:
    elite = RecommendationExplanationBuilder.build(fake())
    assert elite.headline == "ELITE PICK"
    assert elite.stars == 5
    assert elite.score_text == "93/100"
    assert elite.survival_text == "14%"
    assert elite.tier_text == "T4 • LAST"
    assert elite.pass_cost_text == "+12.4 pts"
    assert any("Last available player" in reason for reason in elite.reasons)
    assert any("14%" in reason for reason in elite.reasons)
    assert any("12.4" in reason for reason in elite.reasons)

    safe = RecommendationExplanationBuilder.build(
        fake(
            score=68,
            grade="B",
            survival_probability=0.82,
            is_last_in_tier=False,
            players_remaining_in_tier=5,
            opportunity_cost=-7.0,
            projection_advantage=0.0,
            roster_fit_score=0.0,
            strategy_fit_label="Neutral",
        )
    )
    assert safe.headline == "SOLID OPTION"
    assert any("82%" in reason for reason in safe.reasons)
    assert any("Passing currently projects" in reason for reason in safe.reasons)

    alt = fake(player_name="Alt Player", score=81, survival_probability=0.63)
    with_alt = RecommendationExplanationBuilder.build(fake(), [alt])
    assert with_alt.alternatives
    assert "Alt Player" in with_alt.alternatives[0]

    print("PASS  explanation headline/grade")
    print("PASS  deterministic why-this-pick rules")
    print("PASS  wait/pass-cost language")
    print("PASS  alternatives formatting")
    print()
    print("ALL RECOMMENDATION EXPLANATION TESTS PASSED")


if __name__ == "__main__":
    main()
