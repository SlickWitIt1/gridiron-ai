from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from preferences import normalize_name
from team import base_position


class DraftPickCard(QFrame):
    """One rich draft-board card with lightweight hover intelligence."""

    hovered = Signal(object)
    hover_ended = Signal()

    def __init__(
        self,
        *,
        overall_pick: int,
        round_number: int,
        pick_in_round: int,
        team_number: int,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.overall_pick = overall_pick
        self.round_number = round_number
        self.pick_in_round = pick_in_round
        self.team_number = team_number

        self._draft_pick = None
        self._projection = None
        self._is_my_guy = False
        self._is_current = False
        self._pulse_on = False

        self.setObjectName("DraftPickCard")
        self.setProperty("position", "empty")
        self.setProperty("userTeam", "false")
        self.setProperty("currentPick", "false")
        self.setProperty("pulse", "false")
        self.setProperty("hovered", "false")
        self.setMinimumSize(148, 82)
        self.setMaximumHeight(96)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(650)
        self._pulse_timer.timeout.connect(self._toggle_pulse)

        self._build_ui()
        self.show_empty()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        self.pick_label = QLabel()
        self.pick_label.setObjectName("DraftCardPick")
        top_row.addWidget(self.pick_label)
        top_row.addStretch(1)

        self.my_guy_badge = QLabel("★")
        self.my_guy_badge.setObjectName("DraftCardMyGuyBadge")
        self.my_guy_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.my_guy_badge.hide()
        top_row.addWidget(self.my_guy_badge)

        self.clock_badge = QLabel("ON CLOCK")
        self.clock_badge.setObjectName("DraftCardClockBadge")
        self.clock_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_badge.hide()
        top_row.addWidget(self.clock_badge)

        layout.addLayout(top_row)

        self.player_label = QLabel()
        self.player_label.setObjectName("DraftCardPlayer")
        self.player_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.player_label.setWordWrap(False)
        layout.addWidget(self.player_label)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        self.position_label = QLabel()
        self.position_label.setObjectName("DraftCardPosition")
        meta_row.addWidget(self.position_label)

        self.team_label = QLabel()
        self.team_label.setObjectName("DraftCardTeam")
        meta_row.addWidget(self.team_label)

        meta_row.addStretch(1)

        layout.addLayout(meta_row)

    def show_empty(self) -> None:
        self._draft_pick = None
        self._projection = None
        self._is_my_guy = False

        self.pick_label.setText(f"{self.round_number}.{self.pick_in_round:02d}")
        self.player_label.clear()
        self.position_label.clear()
        self.team_label.clear()
        self.my_guy_badge.hide()
        self.setProperty("position", "empty")
        self._refresh_style()

    def show_player(
        self,
        draft_pick,
        approved_players: set[str],
        projection=None,
    ) -> None:
        self._draft_pick = draft_pick
        self._projection = projection

        player = draft_pick.player
        position = base_position(player.position)
        self._is_my_guy = normalize_name(player.name) in approved_players

        self.pick_label.setText(f"{self.round_number}.{self.pick_in_round:02d}")
        self.player_label.setText(player.name)
        self.position_label.setText(player.position)
        self.team_label.setText(player.team)
        self.setProperty("position", position.lower())

        if self._is_my_guy:
            self.my_guy_badge.show()
        else:
            self.my_guy_badge.hide()

        self._refresh_style()

    def hover_payload(self) -> dict[str, object] | None:
        if self._draft_pick is None:
            return None

        player = self._draft_pick.player
        return {
            "name": player.name,
            "position": player.position,
            "team": player.team,
            "rank": getattr(player, "rank", None),
            "tier": getattr(player, "tier", None),
            "bye": getattr(player, "bye", None),
            "projected_points": getattr(self._projection, "fantasy_points", None),
            "is_my_guy": self._is_my_guy,
            "round_number": self.round_number,
            "pick_in_round": self.pick_in_round,
        }

    def set_user_team(self, enabled: bool) -> None:
        self.setProperty("userTeam", "true" if enabled else "false")
        self._refresh_style()

    def set_current_pick(self, enabled: bool) -> None:
        self._is_current = enabled
        self.setProperty("currentPick", "true" if enabled else "false")

        if enabled:
            self.clock_badge.show()
            self._pulse_on = True
            self.setProperty("pulse", "true")
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self.clock_badge.hide()
            self._pulse_on = False
            self.setProperty("pulse", "false")

        self._refresh_style()

    def _toggle_pulse(self) -> None:
        if not self._is_current:
            return
        self._pulse_on = not self._pulse_on
        self.setProperty("pulse", "true" if self._pulse_on else "false")
        self._refresh_style()

    def _refresh_style(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def enterEvent(self, event: QEvent) -> None:
        self.setProperty("hovered", "true")
        self._refresh_style()
        payload = self.hover_payload()
        if payload is not None:
            self.hovered.emit(payload)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setProperty("hovered", "false")
        self._refresh_style()
        if self._draft_pick is not None:
            self.hover_ended.emit()
        super().leaveEvent(event)
