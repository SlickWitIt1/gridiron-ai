from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from asset_manager import short_player_name
from live_draft import LiveDraftSession
from preferences import normalize_name
from team import base_position


POSITION_FILTERS = ("ALL", "QB", "RB", "WR", "TE", "DST", "K")
POSITION_COLORS = {
    "QB": "#c084fc",
    "RB": "#6ee7b7",
    "WR": "#7dd3fc",
    "TE": "#fdba74",
    "DST": "#cbd5e1",
    "K": "#fde047",
}


class DraftRoomControls(QFrame):
    """Compact live-draft controls that sit directly under the draft board."""

    record_requested = Signal(str)
    undo_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DraftRoomControls")

        self._session: LiveDraftSession | None = None
        self._approved_players: set[str] = set()

        self._build_ui()

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(12)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        heading = QLabel("LIVE DRAFT CONTROLS")
        heading.setObjectName("DraftControlHeading")
        left_layout.addWidget(heading)

        self.turn_label = QLabel("No active draft")
        self.turn_label.setObjectName("DraftControlTurn")
        self.turn_label.setWordWrap(True)
        left_layout.addWidget(self.turn_label)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("DraftControlSearch")
        self.search_input.setPlaceholderText("Search available player…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._refresh_player_list)
        search_row.addWidget(self.search_input, 1)

        self.position_filter = QComboBox()
        self.position_filter.setObjectName("DraftControlPosition")
        self.position_filter.addItems(POSITION_FILTERS)
        self.position_filter.currentTextChanged.connect(self._refresh_player_list)
        search_row.addWidget(self.position_filter)

        left_layout.addLayout(search_row)
        left.setMinimumWidth(330)
        left.setMaximumWidth(440)
        outer.addWidget(left)

        self.available_list = QListWidget()
        self.available_list.setObjectName("DraftControlPlayerList")
        self.available_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.available_list.setUniformItemSizes(True)
        self.available_list.setSpacing(1)
        self.available_list.itemSelectionChanged.connect(self._update_selection_state)
        self.available_list.itemDoubleClicked.connect(self._double_click_record)
        outer.addWidget(self.available_list, 1)

        actions = QWidget()
        action_layout = QVBoxLayout(actions)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(6)

        selected_title = QLabel("SELECTED")
        selected_title.setObjectName("DraftControlMiniHeading")
        action_layout.addWidget(selected_title)

        self.selected_label = QLabel("Choose a player")
        self.selected_label.setObjectName("DraftControlSelected")
        self.selected_label.setWordWrap(True)
        self.selected_label.setMinimumWidth(190)
        action_layout.addWidget(self.selected_label)

        action_layout.addStretch(1)

        self.record_button = QPushButton("RECORD PICK")
        self.record_button.setObjectName("DraftControlPrimaryButton")
        self.record_button.setMinimumHeight(34)
        self.record_button.setEnabled(False)
        self.record_button.clicked.connect(self._record_selected)
        action_layout.addWidget(self.record_button)

        self.undo_button = QPushButton("UNDO LAST PICK")
        self.undo_button.setObjectName("DraftControlSecondaryButton")
        self.undo_button.setMinimumHeight(30)
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_requested.emit)
        action_layout.addWidget(self.undo_button)

        hint = QLabel("Double-click a player to record instantly")
        hint.setObjectName("DraftControlHint")
        hint.setWordWrap(True)
        action_layout.addWidget(hint)

        actions.setMaximumWidth(230)
        outer.addWidget(actions)

        self.setMinimumHeight(156)
        self.setMaximumHeight(190)

    def refresh(self, session: LiveDraftSession | None, approved_players: set[str]) -> None:
        self._session = session
        self._approved_players = set(approved_players)

        if session is None:
            self.turn_label.setText("No active draft")
            self.available_list.clear()
            self.record_button.setEnabled(False)
            self.undo_button.setEnabled(False)
            self.selected_label.setText("Choose a player")
            return

        if session.is_complete:
            self.turn_label.setText("Draft complete")
        elif session.is_user_turn:
            self.turn_label.setText(
                f"YOU'RE ON THE CLOCK  •  PICK {session.current_pick}\n"
                "Select the player who was drafted, or use this panel to enter your own pick."
            )
        else:
            self.turn_label.setText(
                f"TEAM {session.current_team_number} ON CLOCK  •  PICK {session.current_pick}\n"
                "Search or double-click the player selected in the live draft."
            )

        self.undo_button.setEnabled(bool(session.draft_results))
        self._refresh_player_list()

    def selected_player_name(self) -> str | None:
        selected = self.available_list.selectedItems()
        if len(selected) != 1:
            return None
        value = selected[0].data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def _refresh_player_list(self) -> None:
        previously_selected = self.selected_player_name()
        self.available_list.setUpdatesEnabled(False)
        self.available_list.blockSignals(True)
        try:
            self.available_list.clear()
            if self._session is None or self._session.is_complete:
                return

            query = normalize_name(self.search_input.text())
            wanted_position = self.position_filter.currentText().upper()

            for player in self._session.available_players():
                position = base_position(player.position).upper()
                if wanted_position != "ALL" and position != wanted_position:
                    continue
                if query and query not in normalize_name(player.name):
                    continue

                compact_name = short_player_name(player.name)
                rank_text = f"#{player.rank}" if getattr(player, "rank", None) else "—"
                star = "  ★" if normalize_name(player.name) in self._approved_players else ""
                text = f"{compact_name:<22}  {player.position:<5} {player.team:<4}  {rank_text}{star}"

                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, player.name)
                item.setForeground(QColor(POSITION_COLORS.get(position, "#e2e8f0")))
                self.available_list.addItem(item)

                if previously_selected and player.name == previously_selected:
                    item.setSelected(True)
                    self.available_list.setCurrentItem(item)
        finally:
            self.available_list.blockSignals(False)
            self.available_list.setUpdatesEnabled(True)

        self._update_selection_state()

    def _update_selection_state(self) -> None:
        player_name = self.selected_player_name()
        can_record = (
            player_name is not None
            and self._session is not None
            and not self._session.is_complete
        )
        self.record_button.setEnabled(can_record)

        if player_name is None or self._session is None:
            self.selected_label.setText("Choose a player")
            return

        player = self._session.player_for_name(player_name)
        if player is None:
            self.selected_label.setText(player_name)
            return

        my_guy = "  •  ★ MY GUY" if normalize_name(player.name) in self._approved_players else ""
        self.selected_label.setText(
            f"{player.name}\n{player.position}  •  {player.team}  •  Rank {player.rank}{my_guy}"
        )

    def _record_selected(self) -> None:
        player_name = self.selected_player_name()
        if player_name:
            self.record_requested.emit(player_name)

    def _double_click_record(self, item: QListWidgetItem) -> None:
        player_name = item.data(Qt.ItemDataRole.UserRole)
        if player_name:
            self.record_requested.emit(str(player_name))
