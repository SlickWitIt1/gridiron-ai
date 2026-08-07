from collections import Counter, defaultdict
from collections.abc import Iterable

from forecast import DraftForecast, PlayerForecast, PositionForecast, TierForecast
from loader import load_players
from preferences import load_my_guys, normalize_name
from projection_loader import load_projections
from simulation import Simulation
from team import base_position
from tier_engine import TierEngine


TRACKED_POSITIONS = ("RB", "WR", "QB", "TE")


class ForecastEngine:
    """Forecast draft activity between the user's current and next selections."""

    def __init__(
        self,
        players=None,
        approved_players: set[str] | None = None,
        projections=None,
    ) -> None:
        self.players = list(players) if players is not None else load_players()
        self.approved_players = (
            approved_players
            if approved_players is not None
            else load_my_guys()
        )
        self.projections = (
            projections
            if projections is not None
            else load_projections()
        )
        self.tier_engine = TierEngine(self.projections)

    def forecast(
        self,
        *,
        draft_slot: int,
        completed_player_names: tuple[str, ...],
        current_pick: int,
        next_user_pick: int,
        simulations: int = 100,
        player_names: Iterable[str] = (),
    ) -> DraftForecast:
        if simulations <= 0:
            raise ValueError("Forecast simulations must be greater than zero.")
        if next_user_pick <= current_pick:
            raise ValueError("Next user pick must be later than the current pick.")
        if current_pick != len(completed_player_names) + 1:
            raise ValueError(
                "Current pick does not match the completed draft history."
            )

        picks_between = max(0, next_user_pick - current_pick - 1)
        completed_normalized = {
            normalize_name(name) for name in completed_player_names
        }
        available_names = tuple(
            player.name
            for player in self.players
            if normalize_name(player.name) not in completed_normalized
        )
        current_tiers = self.tier_engine.build_tiers(
            available_names=available_names
        )

        requested_players = tuple(dict.fromkeys(player_names))
        requested_normalized = {
            normalize_name(name): name for name in requested_players
        }

        position_pick_totals: Counter[str] = Counter()
        position_selected_counts: Counter[str] = Counter()
        run_counts: Counter[str] = Counter()
        player_survived_counts: Counter[str] = Counter()
        tier_survived_counts: Counter[tuple[str, int]] = Counter()

        tier_members: dict[tuple[str, int], set[str]] = defaultdict(set)
        tier_remaining_now: dict[tuple[str, int], int] = {}
        for normalized_name, info in current_tiers.items():
            key = (info.position, info.tier_number)
            tier_members[key].add(normalized_name)
            tier_remaining_now[key] = max(
                tier_remaining_now.get(key, 0),
                info.players_remaining,
            )

        for seed in range(simulations):
            simulation = Simulation(
                user_team_number=draft_slot,
                seed=seed,
                players=self.players,
                approved_players=self.approved_players,
                initial_player_names=completed_player_names,
            )
            simulation.run(
                print_picks=False,
                max_overall_pick=next_user_pick - 1,
            )

            interval_picks = [
                pick
                for pick in simulation.engine.draft_results
                if current_pick < pick.overall < next_user_pick
            ]
            interval_positions = [
                base_position(pick.player.position)
                for pick in interval_picks
                if base_position(pick.player.position) in TRACKED_POSITIONS
            ]
            interval_counts = Counter(interval_positions)

            for position in TRACKED_POSITIONS:
                count = interval_counts.get(position, 0)
                position_pick_totals[position] += count
                if count > 0:
                    position_selected_counts[position] += 1

            if interval_positions:
                run_position, run_count = interval_counts.most_common(1)[0]
                required_for_run = max(2, round(len(interval_positions) * 0.40))
                if run_count >= required_for_run:
                    run_counts[run_position] += 1

            available_at_next = {
                normalize_name(player.name)
                for player in simulation.board.available_players
            }

            for normalized_name in requested_normalized:
                if normalized_name in available_at_next:
                    player_survived_counts[normalized_name] += 1

            for key, member_names in tier_members.items():
                if member_names & available_at_next:
                    tier_survived_counts[key] += 1

        position_forecasts = tuple(
            PositionForecast(
                position=position,
                expected_picks=(position_pick_totals[position] / simulations),
                probability_selected=(position_selected_counts[position] / simulations),
                run_probability=(run_counts[position] / simulations),
            )
            for position in TRACKED_POSITIONS
        )

        most_likely_run = None
        run_probability = 0.0
        if run_counts:
            most_likely_run, run_occurrences = run_counts.most_common(1)[0]
            run_probability = run_occurrences / simulations
            if run_probability < 0.25:
                most_likely_run = None

        player_forecasts = tuple(
            PlayerForecast(
                player_name=display_name,
                survival_probability=(
                    player_survived_counts[normalized_name] / simulations
                ),
            )
            for normalized_name, display_name in requested_normalized.items()
        )

        tier_forecasts = tuple(
            TierForecast(
                position=position,
                tier_number=tier_number,
                survival_probability=(tier_survived_counts[key] / simulations),
                disappearance_probability=(
                    1.0 - tier_survived_counts[key] / simulations
                ),
                players_remaining_now=tier_remaining_now.get(key, 0),
            )
            for key in sorted(tier_members)
            for position, tier_number in (key,)
        )

        return DraftForecast(
            simulations=simulations,
            current_pick=current_pick,
            next_user_pick=next_user_pick,
            picks_between=picks_between,
            position_forecasts=position_forecasts,
            most_likely_run=most_likely_run,
            run_probability=run_probability,
            player_forecasts=player_forecasts,
            tier_forecasts=tier_forecasts,
        )
