from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from preferences import normalize_name
from team import base_position


POSITION_COLORS = {
    "QB": "#a855f7",
    "RB": "#34d399",
    "WR": "#38bdf8",
    "TE": "#fb923c",
    "DST": "#94a3b8",
    "K": "#facc15",
}

POSITION_TINTS = {
    "QB": "#2a1736",
    "RB": "#153029",
    "WR": "#132c38",
    "TE": "#342315",
    "DST": "#222a34",
    "K": "#332f13",
}


class DraftPickCard(QFrame):
    """Sleeper-inspired draft card for one overall selection."""

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
        self._is_current = False
        self._pulse_on = False

        self.setObjectName("DraftPickCard")
        self.setProperty("position", "empty")
        self.setProperty("userTeam", "false")
        self.setProperty("currentPick", "false")
        self.setProperty("pulse", "false")
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
        top_row.setSpacing(6)

        self.pick_label = QLabel()
        self.pick_label.setObjectName("DraftCardPick")
        top_row.addWidget(self.pick_label)

        top_row.addStretch(1)

        self.badge_label = QLabel()
        self.badge_label.setObjectName("DraftCardBadge")
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.hide()
        top_row.addWidget(self.badge_label)

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
        self.pick_label.setText(f"{self.round_number}.{self.pick_in_round:02d}")
        self.player_label.setText("")
        self.position_label.setText("")
        self.team_label.setText("")
        self.badge_label.hide()
        self.setProperty("position", "empty")
        self.setToolTip(
            f"Overall Pick {self.overall_pick} • Round {self.round_number} • Team {self.team_number}"
        )
        self._refresh_style()

    def show_player(self, draft_pick, approved_players: set[str]) -> None:
        player = draft_pick.player
        position = base_position(player.position)

        self.pick_label.setText(f"{self.round_number}.{self.pick_in_round:02d}")
        self.player_label.setText(player.name)
        self.position_label.setText(player.position)
        self.team_label.setText(player.team)
        self.setProperty("position", position.lower())

        if normalize_name(player.name) in approved_players:
            self.badge_label.setText("★")
            self.badge_label.setProperty("kind", "myGuy")
            self.badge_label.show()
        else:
            self.badge_label.hide()

        self.setToolTip(
            f"{player.name} • {player.position} • {player.team} • "
            f"Overall {self.overall_pick} • Round {self.round_number}"
        )
        self._refresh_style()

    def set_user_team(self, enabled: bool) -> None:
        self.setProperty("userTeam", "true" if enabled else "false")
        self._refresh_style()

    def set_current_pick(self, enabled: bool) -> None:
        self._is_current = enabled
        self.setProperty("currentPick", "true" if enabled else "false")

        if enabled:
            self.badge_label.setText("ON CLOCK")
            self.badge_label.setProperty("kind", "clock")
            self.badge_label.show()
            self._pulse_on = True
            self.setProperty("pulse", "true")
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._pulse_on = False
            self.setProperty("pulse", "false")
            if self.badge_label.property("kind") == "clock":
                self.badge_label.hide()

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
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setProperty("hovered", "false")
        self._refresh_style()
        super().leaveEvent(event)
