from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from player import Player
from recommendation_engine import RecommendationEngine
from recommendation_score import RecommendationScore
from strategy import DraftStrategy, StrategyResult
from team import Team
from tier import TierInfo


def player(name: str, position: str) -> Player:
    return Player(
        rank=10,
        tier=1,
        name=name,
        position=position,
        team="TST",
        bye=0,
        upside="",
        bust="",
        sos="",
    )


def result(strategy: DraftStrategy, priorities: tuple[str, ...]) -> StrategyResult:
    return StrategyResult(
        primary_strategy=strategy,
        secondary_strategy=DraftStrategy.BALANCED,
        confidence=80,
        next_priorities=priorities,
        explanation="test",
        scores=(),
    )


def tier(position: str, urgency: str = "LOW") -> TierInfo:
    return TierInfo(
        player_name="Candidate",
        position=position,
        tier_number=2,
        tier_size=3,
        players_remaining=2,
        projected_points=250.0,
        drop_to_next_tier=4.0,
        urgency=urgency,
        is_last_in_tier=False,
    )


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS  {name}")


def main() -> None:
    team = Team(7)
    team.add_player(player("Anchor RB", "RB1"))
    team.add_player(player("Wideout One", "WR1"))
    team.add_player(player("Wideout Two", "WR2"))

    hero = result(
        DraftStrategy.HERO_RB,
        ("WR", "TE or QB value", "Second RB only at tier value"),
    )

    wr_score, wr_label, _ = RecommendationEngine.strategy_fit(
        hero, team, "WR", tier("WR")
    )
    rb_score, rb_label, _ = RecommendationEngine.strategy_fit(
        hero, team, "RB", tier("RB")
    )
    rb_cliff_score, rb_cliff_label, _ = RecommendationEngine.strategy_fit(
        hero, team, "RB", tier("RB", urgency="CRITICAL")
    )

    check("Hero RB prefers WR", wr_score > rb_score and wr_label == "EXCELLENT")
    check("Hero RB discourages ordinary RB", rb_label == "POOR")
    check(
        "Tier cliff can justify strategy exception",
        rb_cliff_score > rb_score and rb_cliff_label == "VALUE EXCEPTION",
    )

    undetermined = result(DraftStrategy.UNDETERMINED, ("Best Value",))
    neutral_score, neutral_label, _ = RecommendationEngine.strategy_fit(
        undetermined, team, "RB", tier("RB")
    )
    check("Undetermined strategy is neutral", neutral_score == 5.0 and neutral_label == "NEUTRAL")

    score = RecommendationScore(
        total=100.0,
        projection=28.0,
        wait_risk=15.0,
        roster_fit=15.0,
        scarcity=8.0,
        tier_drop=10.0,
        opportunity_cost=9.0,
        strategy_fit=10.0,
        preference=5.0,
        confidence=90,
    )
    check("Score components sum to 100", score.components_total == 100.0)
    check("Eight visible score components", len(score.component_items()) == 8)

    print("\nALL STRATEGY RECOMMENDATION TESTS PASSED")


if __name__ == "__main__":
    main()
