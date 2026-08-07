from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from draft_pick import DraftPick
from player import Player
from strategy import DraftStrategy
from strategy_engine import StrategyEngine
from team import Team


def player(rank: int, tier: int, name: str, position: str) -> Player:
    return Player(
        rank=rank,
        tier=tier,
        name=name,
        position=position,
        team="TST",
        bye=0,
        upside="",
        bust="",
        sos="",
    )


def analyze(players: list[Player]):
    team = Team(7)
    picks: list[DraftPick] = []
    for index, selected in enumerate(players, start=1):
        team.add_player(selected)
        picks.append(
            DraftPick(
                overall=index,
                round_number=index,
                pick_in_round=7,
                team_number=7,
                player=selected,
            )
        )
    return StrategyEngine().analyze(team, picks)


def check(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")
    print(f"PASS  {name}")


def main() -> None:
    rb1 = player(3, 1, "Anchor RB", "RB1")
    rb2 = player(14, 2, "Second RB", "RB7")
    rb3 = player(28, 3, "Third RB", "RB14")
    wr1 = player(5, 1, "Alpha WR", "WR1")
    wr2 = player(16, 2, "Second WR", "WR8")
    wr3 = player(29, 3, "Third WR", "WR15")
    wr4 = player(46, 4, "Fourth WR", "WR24")
    qb1 = player(22, 1, "Elite QB", "QB1")
    qb_late = player(95, 6, "Ordinary QB", "QB12")
    te1 = player(18, 1, "Elite TE", "TE1")

    check(
        "empty roster",
        analyze([]).primary_strategy,
        DraftStrategy.UNDETERMINED,
    )
    check(
        "two picks remains undetermined",
        analyze([rb1, wr1]).primary_strategy,
        DraftStrategy.UNDETERMINED,
    )
    check(
        "hero RB",
        analyze([rb1, wr1, wr2, te1]).primary_strategy,
        DraftStrategy.HERO_RB,
    )
    zero_result = analyze([wr1, wr2, te1, wr3, wr4])
    check("zero RB", zero_result.primary_strategy, DraftStrategy.ZERO_RB)
    check("zero RB early priority", zero_result.next_priority, "Best Value")
    check(
        "robust RB",
        analyze([rb1, rb2, wr1, rb3]).primary_strategy,
        DraftStrategy.ROBUST_RB,
    )
    check(
        "WR heavy",
        analyze([wr1, wr2, wr3, rb1, wr4]).primary_strategy,
        DraftStrategy.WR_HEAVY,
    )
    check(
        "elite QB",
        analyze([qb1, wr1, rb1]).primary_strategy,
        DraftStrategy.ELITE_QB,
    )
    check(
        "ordinary QB is not elite QB",
        analyze([qb_late, wr1, rb1]).primary_strategy,
        DraftStrategy.BALANCED,
    )
    check(
        "elite TE",
        analyze([te1, wr1, rb1]).primary_strategy,
        DraftStrategy.ELITE_TE,
    )
    check(
        "balanced",
        analyze([rb1, wr1, qb_late, te1]).primary_strategy,
        DraftStrategy.BALANCED,
    )

    ambiguous = analyze([rb1, wr1, wr2])
    if ambiguous.secondary_strategy is None:
        raise AssertionError("ambiguous result should expose a secondary strategy")
    print("PASS  secondary strategy exposed")

    if not 0 <= ambiguous.confidence <= 99:
        raise AssertionError("confidence must be between 0 and 99")
    print("PASS  confidence range")

    print("\nALL STRATEGY ENGINE TESTS PASSED")


if __name__ == "__main__":
    main()
