from time import perf_counter

from PySide6.QtCore import QObject, Signal

from coach_engine import CoachEngine
from forecast_engine import ForecastEngine
from preferences import normalize_name
from projection_loader import load_projections
from recommendation_engine import RecommendationEngine
from strategy_engine import StrategyEngine
from wait_analyzer import WaitAnalysis, WaitAnalyzer


class RecommendationWorker(QObject):
    finished = Signal(object, object, object, float)
    failed = Signal(str)

    def __init__(
        self,
        candidate_names: tuple[str, ...],
        draft_slot: int,
        completed_player_names: tuple[str, ...],
        current_pick: int,
        next_pick: int | None,
        simulations: int,
        user_team,
        draft_picks=(),
        previous_recommendation=None,
        previous_forecast=None,
        selected_player_name: str | None = None,
    ) -> None:
        super().__init__()

        self.candidate_names = candidate_names
        self.draft_slot = draft_slot
        self.completed_player_names = completed_player_names
        self.current_pick = current_pick
        self.next_pick = next_pick
        self.simulations = simulations
        self.user_team = user_team
        self.draft_picks = tuple(draft_picks)
        self.previous_recommendation = previous_recommendation
        self.previous_forecast = previous_forecast
        self.selected_player_name = selected_player_name

    def run(self) -> None:
        try:
            start_time = perf_counter()

            wait_analyzer = WaitAnalyzer()
            projections = load_projections()

            completed_names = {
                normalize_name(player_name)
                for player_name in self.completed_player_names
            }
            available_player_names = tuple(
                player.name
                for player in wait_analyzer.players
                if normalize_name(player.name) not in completed_names
            )

            recommendation_engine = RecommendationEngine(
                players=wait_analyzer.players,
                projections=projections,
                approved_players=wait_analyzer.approved_players,
            )

            strategy_result = StrategyEngine().analyze(
                roster=self.user_team,
                draft_picks=self.draft_picks,
            )

            # -----------------------------------------------------------------
            # STAGE 1 — WIDE FUNNEL
            #
            # Screen a broad set of serious candidates with a lighter simulation
            # count. This prevents player #11 or #17 from being excluded before
            # the expensive counterfactual analysis ever sees him.
            # -----------------------------------------------------------------
            broad_names = tuple(self.candidate_names)

            if self.next_pick is not None:
                shallow_simulations = max(
                    20,
                    min(30, max(1, self.simulations // 4)),
                )

                shallow_forecast = ForecastEngine(
                    players=wait_analyzer.players,
                    approved_players=wait_analyzer.approved_players,
                    projections=projections,
                ).forecast(
                    draft_slot=self.draft_slot,
                    completed_player_names=self.completed_player_names,
                    current_pick=self.current_pick,
                    next_user_pick=self.next_pick,
                    simulations=shallow_simulations,
                    player_names=broad_names,
                )

                shallow_wait = wait_analyzer.analyze_live_players(
                    player_names=broad_names,
                    draft_slot=self.draft_slot,
                    completed_player_names=self.completed_player_names,
                    current_pick=self.current_pick,
                    next_pick=self.next_pick,
                    simulations=shallow_simulations,
                )

                preliminary = recommendation_engine.recommend(
                    wait_results=shallow_wait,
                    user_team=self.user_team,
                    available_player_names=available_player_names,
                    strategy_result=strategy_result,
                    forecast=shallow_forecast,
                )

                # Keep enough finalists to preserve positional diversity while
                # making the expensive second stage fast enough for live use.
                finalist_limit = min(
                    8,
                    len(preliminary),
                )
                finalist_names = tuple(
                    recommendation.player_name
                    for recommendation in preliminary[:finalist_limit]
                )

                # Defensive fallback: if preliminary scoring somehow returns
                # nothing, don't silently abandon the user's candidate pool.
                if not finalist_names:
                    finalist_names = broad_names[:8]

                # -------------------------------------------------------------
                # STAGE 2 — DEEP FINAL
                #
                # Full simulation depth only on the strongest finalists.
                # -------------------------------------------------------------
                forecast = ForecastEngine(
                    players=wait_analyzer.players,
                    approved_players=wait_analyzer.approved_players,
                    projections=projections,
                ).forecast(
                    draft_slot=self.draft_slot,
                    completed_player_names=self.completed_player_names,
                    current_pick=self.current_pick,
                    next_user_pick=self.next_pick,
                    simulations=self.simulations,
                    player_names=finalist_names,
                )

                wait_results = wait_analyzer.analyze_live_players(
                    player_names=finalist_names,
                    draft_slot=self.draft_slot,
                    completed_player_names=self.completed_player_names,
                    current_pick=self.current_pick,
                    next_pick=self.next_pick,
                    simulations=self.simulations,
                )

                recommendations = recommendation_engine.recommend(
                    wait_results=wait_results,
                    user_team=self.user_team,
                    available_player_names=available_player_names,
                    strategy_result=strategy_result,
                    forecast=forecast,
                )

            else:
                # Final user pick: no next-pick counterfactual exists. The broad
                # candidate pool can be scored directly from value/roster/tier/
                # strategy/preferences without wasting simulation work.
                wait_results = [
                    WaitAnalysis(
                        player_name=player_name,
                        simulations=1,
                        available_now_count=1,
                        survived_count=0,
                    )
                    for player_name in broad_names
                ]

                forecast = None
                recommendations = recommendation_engine.recommend(
                    wait_results=wait_results,
                    user_team=self.user_team,
                    available_player_names=available_player_names,
                    strategy_result=strategy_result,
                    forecast=None,
                )

            if forecast is None:
                coach_message = (
                    "Final pick: recommendation uses roster fit, value, tiers, "
                    "strategy, and preferences."
                )
            elif self.selected_player_name:
                coach_message = CoachEngine.selection_message(
                    selected_player_name=self.selected_player_name,
                    previous_recommendation=self.previous_recommendation,
                    previous_strategy=self.previous_recommendation,
                    current_strategy=strategy_result,
                    previous_forecast=self.previous_forecast,
                    current_forecast=forecast,
                )
            else:
                coach_message = CoachEngine.recommendation_message(
                    recommendations=recommendations,
                    forecast=forecast,
                    strategy_result=strategy_result,
                )

            runtime = perf_counter() - start_time

            self.finished.emit(
                recommendations,
                forecast,
                coach_message,
                runtime,
            )

        except Exception as error:
            self.failed.emit(str(error))
