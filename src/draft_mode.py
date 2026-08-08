from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal

from decision_engine import DecisionEngine


class DraftMode(str, Enum):
    LIVE = "live"
    MOCK = "mock"

    @property
    def display_name(self) -> str:
        return "Live Draft" if self is DraftMode.LIVE else "Mock Draft"


class DraftModeController(QObject):
    """Controls HOW picks enter one shared LiveDraftSession.

    The session remains the single source of truth in every mode. Recommendation,
    forecast, wait, tier, roster, undo/redo, and UI code all read that same state.
    """

    pick_recorded = Signal(object)
    user_turn_ready = Signal()
    draft_complete = Signal()

    mode = DraftMode.LIVE

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session

    def start(self) -> None:
        """Begin mode-specific behavior."""
        if self.session.is_complete:
            self.draft_complete.emit()
        elif self.session.is_user_turn:
            self.user_turn_ready.emit()

    def stop(self) -> None:
        """Hook for controllers with scheduled work."""


class LiveDraftController(DraftModeController):
    """Live mode: humans/manual entry supply every league pick."""

    mode = DraftMode.LIVE


class MockDraftController(DraftModeController):
    """Mock mode: existing DecisionEngine supplies every opponent pick.

    Importantly, this does NOT create a second draft state or a second fantasy
    intelligence stack. AI opponent choices are recorded through the exact same
    session.record_pick() method used in Live Draft.
    """

    mode = DraftMode.MOCK

    def __init__(
        self,
        session,
        parent=None,
        *,
        delay_ms: int = 180,
    ) -> None:
        super().__init__(session, parent)
        self.delay_ms = max(0, int(delay_ms))
        self._decision_engine = DecisionEngine(session.market)
        self._running = False
        self._generation = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        self.advance_until_user_turn()

    def stop(self) -> None:
        self._running = False
        self._generation += 1

    def draft_next_ai_pick(self):
        """Draft exactly one opponent pick. Useful for tests and step control."""
        if (
            self.session.is_complete
            or self.session.is_user_turn
        ):
            return None

        overall_pick = self.session.current_pick
        team_number = self.session.current_team_number
        if team_number is None:
            return None

        team = self.session.league.teams[team_number - 1]
        current_round = (
            (overall_pick - 1)
            // self.session.league.num_teams
        ) + 1

        player = self._decision_engine.choose_player(
            team=team,
            available_players=self.session.board.available_players,
            available_names=self.session.board.available_names,
            current_round=current_round,
            approved_players=None,
            excluded_players=set(),
        )

        if player is None:
            raise RuntimeError(
                f"Mock Team {team_number} had no eligible player "
                f"at Pick {overall_pick}."
            )

        return self.session.record_pick(player.name)

    def advance_until_user_turn(self) -> None:
        """Animate AI picks one-by-one until the draft reaches the user."""
        self.stop()

        if self.session.is_complete:
            self.draft_complete.emit()
            return

        if self.session.is_user_turn:
            self.user_turn_ready.emit()
            return

        self._running = True
        self._generation += 1
        generation = self._generation
        self._schedule_next(generation)

    def _schedule_next(self, generation: int) -> None:
        QTimer.singleShot(
            self.delay_ms,
            lambda: self._advance_one(generation),
        )

    def _advance_one(self, generation: int) -> None:
        if (
            not self._running
            or generation != self._generation
        ):
            return

        if self.session.is_complete:
            self._running = False
            self.draft_complete.emit()
            return

        if self.session.is_user_turn:
            self._running = False
            self.user_turn_ready.emit()
            return

        draft_pick = self.draft_next_ai_pick()
        if draft_pick is not None:
            self.pick_recorded.emit(draft_pick)

        if self.session.is_complete:
            self._running = False
            self.draft_complete.emit()
        elif self.session.is_user_turn:
            self._running = False
            self.user_turn_ready.emit()
        else:
            self._schedule_next(generation)
