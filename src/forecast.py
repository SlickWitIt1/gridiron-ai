from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PositionForecast:
    position: str
    expected_picks: float
    probability_selected: float
    run_probability: float


@dataclass(frozen=True, slots=True)
class PlayerForecast:
    player_name: str
    survival_probability: float


@dataclass(frozen=True, slots=True)
class TierForecast:
    position: str
    tier_number: int
    survival_probability: float
    disappearance_probability: float
    players_remaining_now: int

    @property
    def label(self) -> str:
        return f"{self.position} Tier {self.tier_number}"


@dataclass(frozen=True, slots=True)
class PickForecast:
    overall_pick: int
    team_number: int
    most_likely_position: str | None
    probability: float
    position_probabilities: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class DraftForecast:
    simulations: int
    current_pick: int
    next_user_pick: int
    picks_between: int
    position_forecasts: tuple[PositionForecast, ...]
    most_likely_run: str | None
    run_probability: float
    player_forecasts: tuple[PlayerForecast, ...]
    tier_forecasts: tuple[TierForecast, ...]
    pick_forecasts: tuple[PickForecast, ...]

    def position(self, position: str) -> PositionForecast | None:
        target = position.upper()
        return next(
            (
                forecast
                for forecast in self.position_forecasts
                if forecast.position == target
            ),
            None,
        )

    def pick(self, overall_pick: int) -> PickForecast | None:
        return next(
            (
                forecast
                for forecast in self.pick_forecasts
                if forecast.overall_pick == overall_pick
            ),
            None,
        )

    def player(self, player_name: str) -> PlayerForecast | None:
        target = player_name.casefold().strip()
        return next(
            (
                forecast
                for forecast in self.player_forecasts
                if forecast.player_name.casefold().strip() == target
            ),
            None,
        )
