from time import perf_counter

from PySide6.QtCore import QObject, Signal

from preferences import normalize_name
from projection_loader import load_projections
from recommendation_engine import RecommendationEngine
from wait_analyzer import WaitAnalyzer


class RecommendationWorker(QObject):
    finished = Signal(object, float)
    failed = Signal(str)

    def __init__(
        self,
        candidate_names: tuple[str, ...],
        draft_slot: int,
        completed_player_names: tuple[str, ...],
        current_pick: int,
        next_pick: int,
        simulations: int,
        user_team,
    ) -> None:
        super().__init__()

        self.candidate_names = candidate_names
        self.draft_slot = draft_slot
        self.completed_player_names = completed_player_names
        self.current_pick = current_pick
        self.next_pick = next_pick
        self.simulations = simulations
        self.user_team = user_team

    def run(self) -> None:
        try:
            start_time = perf_counter()

            wait_analyzer = WaitAnalyzer()

            wait_results = wait_analyzer.analyze_live_players(
                player_names=self.candidate_names,
                draft_slot=self.draft_slot,
                completed_player_names=self.completed_player_names,
                current_pick=self.current_pick,
                next_pick=self.next_pick,
                simulations=self.simulations,
            )

            completed_names = {
                normalize_name(player_name)
                for player_name in self.completed_player_names
            }

            available_player_names = tuple(
                player.name
                for player in wait_analyzer.players
                if normalize_name(player.name)
                not in completed_names
            )

            recommendation_engine = RecommendationEngine(
                players=wait_analyzer.players,
                projections=load_projections(),
                approved_players=wait_analyzer.approved_players,
            )

            recommendations = recommendation_engine.recommend(
                wait_results=wait_results,
                user_team=self.user_team,
                available_player_names=available_player_names,
            )

            runtime = perf_counter() - start_time

            self.finished.emit(
                recommendations,
                runtime,
            )

        except Exception as error:
            self.failed.emit(str(error))
