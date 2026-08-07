from collections import defaultdict
from collections.abc import Iterable
from statistics import median

from preferences import normalize_name
from projection import Projection
from tier import TierInfo


class TierEngine:
    """Build projection-based player tiers with robust gap detection."""

    ROBUST_Z_THRESHOLD = 2.5
    MAD_SCALE = 1.4826

    def __init__(
        self,
        projections: dict[str, Projection],
    ) -> None:
        self.projections = projections

    @staticmethod
    def _median_absolute_deviation(
        values: list[float],
    ) -> float:
        if not values:
            return 0.0

        center = median(values)
        deviations = [
            abs(value - center)
            for value in values
        ]

        return median(deviations)

    @classmethod
    def _tier_break_indices(
        cls,
        projections: list[Projection],
    ) -> set[int]:
        """
        Return indexes where a new tier begins.

        Index 0 is always Tier 1. For every later player, the gap from the
        previous player is compared with the other projection gaps at that
        position using a median/MAD robust z-score.
        """
        if len(projections) < 2:
            return {0}

        gaps = [
            max(
                0.0,
                projections[index].fantasy_points
                - projections[index + 1].fantasy_points,
            )
            for index in range(len(projections) - 1)
        ]

        gap_median = median(gaps)
        gap_mad = cls._median_absolute_deviation(gaps)

        break_indices = {0}

        if gap_mad > 0.0:
            robust_scale = gap_mad * cls.MAD_SCALE

            for gap_index, gap in enumerate(gaps):
                robust_z = (
                    gap - gap_median
                ) / robust_scale

                if robust_z >= cls.ROBUST_Z_THRESHOLD:
                    break_indices.add(gap_index + 1)

            return break_indices

        # When every ordinary gap is identical, MAD is zero. In that case,
        # only gaps strictly larger than the common median create a tier.
        for gap_index, gap in enumerate(gaps):
            if gap > gap_median:
                break_indices.add(gap_index + 1)

        return break_indices

    @staticmethod
    def _urgency(
        players_remaining: int,
        drop_to_next_tier: float,
        typical_gap: float,
    ) -> str:
        if players_remaining <= 1 and drop_to_next_tier > 0.0:
            return "CRITICAL"

        if players_remaining <= 2:
            return "HIGH"

        if (
            drop_to_next_tier > 0.0
            and drop_to_next_tier >= typical_gap
        ):
            return "MEDIUM"

        return "LOW"

    def build_tiers(
        self,
        available_names: Iterable[str] | None = None,
    ) -> dict[str, TierInfo]:
        """
        Build TierInfo objects keyed by normalized player name.

        When available_names is supplied, players already drafted are removed
        before tier sizes and players-remaining values are calculated.
        """
        available_normalized = (
            None
            if available_names is None
            else {
                normalize_name(name)
                for name in available_names
            }
        )

        by_position: dict[str, list[Projection]] = defaultdict(list)

        for normalized_name, projection in self.projections.items():
            if (
                available_normalized is not None
                and normalized_name not in available_normalized
            ):
                continue

            by_position[projection.position].append(projection)

        tier_info_by_name: dict[str, TierInfo] = {}

        for position, position_projections in by_position.items():
            position_projections.sort(
                key=lambda projection: (
                    projection.fantasy_points,
                    projection.name,
                ),
                reverse=True,
            )

            if not position_projections:
                continue

            break_indices = self._tier_break_indices(
                position_projections
            )

            tier_groups: list[list[Projection]] = []
            current_group: list[Projection] = []

            for index, projection in enumerate(position_projections):
                if index in break_indices and current_group:
                    tier_groups.append(current_group)
                    current_group = []

                current_group.append(projection)

            if current_group:
                tier_groups.append(current_group)

            all_gaps = [
                max(
                    0.0,
                    position_projections[index].fantasy_points
                    - position_projections[index + 1].fantasy_points,
                )
                for index in range(len(position_projections) - 1)
            ]
            typical_gap = median(all_gaps) if all_gaps else 0.0

            for tier_index, tier_group in enumerate(
                tier_groups,
                start=1,
            ):
                next_tier = (
                    tier_groups[tier_index]
                    if tier_index < len(tier_groups)
                    else None
                )

                drop_to_next_tier = 0.0

                if next_tier:
                    drop_to_next_tier = max(
                        0.0,
                        tier_group[-1].fantasy_points
                        - next_tier[0].fantasy_points,
                    )

                tier_size = len(tier_group)

                for player_index, projection in enumerate(tier_group):
                    players_remaining = tier_size - player_index
                    urgency = self._urgency(
                        players_remaining=players_remaining,
                        drop_to_next_tier=drop_to_next_tier,
                        typical_gap=typical_gap,
                    )

                    tier_info_by_name[
                        normalize_name(projection.name)
                    ] = TierInfo(
                        player_name=projection.name,
                        position=position,
                        tier_number=tier_index,
                        tier_size=tier_size,
                        players_remaining=players_remaining,
                        projected_points=projection.fantasy_points,
                        drop_to_next_tier=drop_to_next_tier,
                        urgency=urgency,
                        is_last_in_tier=(players_remaining == 1),
                    )

        return tier_info_by_name

    def tier_for_player(
        self,
        player_name: str,
        available_names: Iterable[str] | None = None,
    ) -> TierInfo | None:
        tiers = self.build_tiers(
            available_names=available_names
        )

        return tiers.get(
            normalize_name(player_name)
        )
