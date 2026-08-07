import sys

from PySide6.QtCore import QSize, QThread, Qt
from PySide6.QtGui import (
    QAction, QColor, QFontDatabase, QIcon, QKeySequence, QPainter, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from draft_session_store import DraftSessionStore
from live_draft import LiveDraftSession
from preferences import load_my_guys, normalize_name
from ui.command_center_widget import CommandCenterWidget
from ui.draft_board_dialog import DraftBoardDialog
from ui.draft_pulse_widget import DraftPulseWidget
from ui.recommendation_worker import RecommendationWorker
from ui.styles import DARK_STYLESHEET
from ui.war_room_header import WarRoomHeader


DEFAULT_SIMULATIONS = 100

POSITION_FILTERS = (
    "ALL",
    "QB",
    "RB",
    "WR",
    "TE",
    "DST",
    "K",
)



class GridironWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "Gridiron AI"
        )

        self.resize(
            1500,
            900,
        )

        self.setMinimumSize(
            1100,
            700,
        )

        self.store = DraftSessionStore()

        self.session: LiveDraftSession | None = None
        self.simulations = DEFAULT_SIMULATIONS

        self.approved_players = load_my_guys()

        self.available_player_font = QFontDatabase.systemFont(
            QFontDatabase.SystemFont.FixedFont
        )
        self.available_player_font.setPointSize(12)
        self.my_guy_icon = self._make_status_icon("#ffd700")
        self.normal_player_icon = self._make_status_icon("#3b4657")

        self.recommendation_thread: QThread | None = None
        self.recommendation_worker: RecommendationWorker | None = None

        self.current_recommendations = []

        self.draft_board_dialog: (
            DraftBoardDialog | None
        ) = None

        self.setup_ui()
        self.setup_actions()
        self.show_start_screen()

        self.statusBar().showMessage(
            "Gridiron AI ready."
        )

    @staticmethod
    def _make_status_icon(color: str) -> QIcon:
        """Build one tiny cached status dot without per-row widgets."""
        pixmap = QPixmap(14, 14)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawEllipse(3, 3, 8, 8)
        painter.end()

        return QIcon(pixmap)

    def setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        self.main_layout = QVBoxLayout(
            central_widget
        )

        self.main_layout.setContentsMargins(
            16,
            12,
            16,
            12,
        )

        self.main_layout.setSpacing(
            10
        )

        self.war_room_header = WarRoomHeader()
        self.main_layout.addWidget(self.war_room_header)

        # Kept as a hidden compatibility label because the rest of the
        # application still writes status text here. The War Room header
        # is now the visible source of draft-state information.
        self.status_label = QLabel()
        self.status_label.hide()

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setObjectName("WarRoomSplitter")
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setHandleWidth(8)
        self.main_layout.addWidget(self.content_splitter, 1)

        self.left_panel_widget = QWidget()
        self.left_panel_widget.setObjectName("LeftPanel")
        self.middle_panel_widget = QWidget()
        self.middle_panel_widget.setObjectName("MiddlePanel")
        self.right_panel_widget = QWidget()
        self.right_panel_widget.setObjectName("RightPanel")

        self.left_panel = QVBoxLayout(self.left_panel_widget)
        self.middle_panel = QVBoxLayout(self.middle_panel_widget)
        self.right_panel = QVBoxLayout(self.right_panel_widget)

        self.left_panel.setContentsMargins(0, 0, 8, 0)
        self.middle_panel.setContentsMargins(0, 0, 8, 0)
        self.right_panel.setContentsMargins(0, 0, 0, 0)

        self.left_panel.setSpacing(10)
        self.middle_panel.setSpacing(9)
        self.right_panel.setSpacing(8)

        self.left_panel_widget.setMinimumWidth(290)
        self.left_panel_widget.setMaximumWidth(390)
        self.middle_panel_widget.setMinimumWidth(350)
        self.middle_panel_widget.setMaximumWidth(500)
        self.right_panel_widget.setMinimumWidth(560)

        self.content_splitter.addWidget(self.left_panel_widget)
        self.content_splitter.addWidget(self.middle_panel_widget)
        self.content_splitter.addWidget(self.right_panel_widget)
        self.content_splitter.setStretchFactor(0, 0)
        self.content_splitter.setStretchFactor(1, 0)
        self.content_splitter.setStretchFactor(2, 1)
        self.content_splitter.setSizes([325, 420, 755])

        self.setup_left_panel()
        self.setup_middle_panel()
        self.setup_right_panel()

    def setup_actions(self) -> None:
        undo_action = QAction(
            "Undo Last Pick",
            self,
        )

        undo_action.setShortcut(
            QKeySequence.StandardKey.Undo
        )

        undo_action.triggered.connect(
            self.undo_last_pick
        )

        self.addAction(
            undo_action
        )

        board_action = QAction(
            "Open Draft Board",
            self,
        )

        board_action.setShortcut(
            QKeySequence("Ctrl+B")
        )

        board_action.triggered.connect(
            self.open_draft_board
        )

        self.addAction(
            board_action
        )

    def panel_heading(
        self,
        text: str,
    ) -> QLabel:
        label = QLabel(
            text
        )

        label.setObjectName(
            "PanelHeading"
        )

        return label

    def setup_left_panel(self) -> None:
        self.left_panel.addWidget(
            self.panel_heading(
                "Draft Setup"
            )
        )

        self.left_panel.addWidget(
            QLabel(
                "Your draft slot"
            )
        )

        self.slot_selector = QComboBox()
        self.slot_selector.setObjectName("LeftControl")
        self.slot_selector.setFixedHeight(40)

        for slot in range(1, 11):
            self.slot_selector.addItem(
                str(slot)
            )

        self.slot_selector.setCurrentText(
            "7"
        )

        self.left_panel.addWidget(
            self.slot_selector
        )

        self.left_panel.addWidget(
            QLabel(
                "Simulations per candidate"
            )
        )

        self.simulations_selector = QSpinBox()
        self.simulations_selector.setObjectName("LeftControl")
        self.simulations_selector.setFixedHeight(40)

        self.simulations_selector.setRange(
            10,
            10000,
        )

        self.simulations_selector.setValue(
            DEFAULT_SIMULATIONS
        )

        self.left_panel.addWidget(
            self.simulations_selector
        )

        self.new_draft_button = QPushButton(
            "Start New Draft"
        )
        self.new_draft_button.setFixedHeight(30)

        self.new_draft_button.clicked.connect(
            self.start_new_draft
        )

        self.left_panel.addWidget(
            self.new_draft_button
        )

        self.resume_button = QPushButton(
            "Resume Saved Draft"
        )
        self.resume_button.setFixedHeight(30)

        self.resume_button.setObjectName(
            "SecondaryButton"
        )

        self.resume_button.clicked.connect(
            self.resume_saved_draft
        )

        self.left_panel.addWidget(
            self.resume_button
        )

        self.undo_button = QPushButton(
            "Undo Last Pick"
        )
        self.undo_button.setFixedHeight(30)

        self.undo_button.setObjectName(
            "SecondaryButton"
        )

        self.undo_button.clicked.connect(
            self.undo_last_pick
        )

        self.left_panel.addWidget(
            self.undo_button
        )

        self.draft_board_button = QPushButton(
            "Open Draft Board"
        )
        self.draft_board_button.setFixedHeight(30)

        self.draft_board_button.setObjectName(
            "SecondaryButton"
        )

        self.draft_board_button.clicked.connect(
            self.open_draft_board
        )

        self.left_panel.addWidget(
            self.draft_board_button
        )

        self.delete_save_button = QPushButton(
            "Delete Saved Draft"
        )
        self.delete_save_button.setFixedHeight(30)

        self.delete_save_button.setObjectName(
            "DangerButton"
        )

        self.delete_save_button.clicked.connect(
            self.delete_saved_draft
        )

        self.left_panel.addWidget(
            self.delete_save_button
        )

        self.left_panel.addSpacing(
            4
        )

        self.left_panel.addWidget(
            self.panel_heading(
                "Your Roster"
            )
        )

        self.roster_list = QListWidget()

        self.roster_list.setMinimumHeight(170)

        self.left_panel.addWidget(
            self.roster_list,
            1,
        )

        self.roster_summary_label = QLabel()

        self.roster_summary_label.setWordWrap(
            True
        )

        self.left_panel.addWidget(
            self.roster_summary_label
        )

        self.left_panel.addSpacing(
            4
        )

        self.draft_pulse_widget = DraftPulseWidget(
            window_size=10
        )

        self.draft_pulse_widget.setMinimumHeight(158)
        self.draft_pulse_widget.setMaximumHeight(174)

        self.left_panel.addWidget(
            self.draft_pulse_widget,
            0,
        )

    def setup_middle_panel(self) -> None:
        self.middle_panel.addWidget(
            self.panel_heading(
                "Available Players"
            )
        )

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search player..."
        )
        self.search_input.setMinimumHeight(40)

        self.search_input.textChanged.connect(
            self.refresh_available_players
        )

        filter_layout.addWidget(
            self.search_input
        )

        self.position_filter = QComboBox()
        self.position_filter.setObjectName("PositionFilter")
        self.position_filter.setMinimumWidth(112)
        self.position_filter.setFixedHeight(40)

        for position in POSITION_FILTERS:
            self.position_filter.addItem(
                position
            )

        self.position_filter.currentTextChanged.connect(
            self.refresh_available_players
        )

        filter_layout.addWidget(
            self.position_filter
        )

        self.middle_panel.addLayout(
            filter_layout
        )

        self.available_header = QLabel("      RK   POS   PLAYER")
        self.available_header.setObjectName("AvailablePlayersHeader")
        self.available_header.setFont(self.available_player_font)
        self.available_header.setMinimumHeight(30)
        self.middle_panel.addWidget(self.available_header)

        self.available_list = QListWidget()
        self.available_list.setObjectName("AvailablePlayersList")

        self.available_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )

        self.available_list.itemSelectionChanged.connect(
            self.update_selected_players
        )

        self.available_list.itemDoubleClicked.connect(
            self.record_double_clicked_player
        )

        self.available_list.setSpacing(1)
        self.available_list.setUniformItemSizes(True)
        self.available_list.setIconSize(QSize(14, 14))

        self.middle_panel.addWidget(
            self.available_list
        )

        self.selected_player_label = QLabel(
            "Selected candidates: 0"
        )

        self.middle_panel.addWidget(
            self.selected_player_label
        )

        button_layout = QHBoxLayout()

        self.record_pick_button = QPushButton(
            "Record Pick"
        )

        self.record_pick_button.clicked.connect(
            self.record_selected_player
        )

        self.record_pick_button.setEnabled(
            False
        )

        button_layout.addWidget(
            self.record_pick_button
        )

        self.analyze_button = QPushButton(
            "Analyze Selected"
        )

        self.analyze_button.clicked.connect(
            self.analyze_selected_players
        )

        self.analyze_button.setEnabled(
            False
        )

        button_layout.addWidget(
            self.analyze_button
        )

        self.middle_panel.addLayout(
            button_layout
        )

        legend = QLabel(
            '<span style="color:#ffd700;">●</span> My Guy'
            '   •   Double-click a player to record the pick'
        )
        legend.setTextFormat(Qt.TextFormat.RichText)
        legend.setObjectName("PlayerLegend")

        self.middle_panel.addWidget(
            legend
        )

    def setup_right_panel(self) -> None:
        self.command_center = CommandCenterWidget()

        self.recommendation_status_label = (
            self.command_center.status_label
        )
        self.recommendation_table = (
            self.command_center.table
        )
        self.reason_label = (
            self.command_center.reason_label
        )

        self.recommendation_table.itemSelectionChanged.connect(
            self.show_selected_recommendation
        )

        self.right_panel.addWidget(
            self.command_center
        )

    def show_start_screen(self) -> None:
        self.session = None
        self.current_recommendations = []

        self.status_label.setText(
            "Start a new draft or resume a saved session."
        )
        self.war_room_header.reset()
        self.draft_pulse_widget.reset()

        self.available_list.clear()
        self.roster_list.clear()

        self.recommendation_table.setSortingEnabled(
            False
        )

        self.recommendation_table.setRowCount(
            0
        )

        self.recommendation_table.setSortingEnabled(
            True
        )

        self.selected_player_label.setText(
            "Selected candidates: 0"
        )

        self.roster_summary_label.setText(
            "No active draft."
        )

        self.command_center.reset()

        self.record_pick_button.setEnabled(
            False
        )

        self.analyze_button.setEnabled(
            False
        )

        self.undo_button.setEnabled(
            False
        )

        self.draft_board_button.setEnabled(
            False
        )

        self.resume_button.setEnabled(
            self.store.exists()
        )

        self.delete_save_button.setEnabled(
            self.store.exists()
        )

    def start_new_draft(self) -> None:
        if self.store.exists():
            choice = QMessageBox.question(
                self,
                "Replace saved draft?",
                (
                    "A saved draft already exists. "
                    "Start over and replace it?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if choice != QMessageBox.StandardButton.Yes:
                return

            self.store.delete()

        draft_slot = int(
            self.slot_selector.currentText()
        )

        self.simulations = (
            self.simulations_selector.value()
        )

        self.session = LiveDraftSession(
            user_team_number=draft_slot
        )

        self.clear_recommendations()
        self.save_active_session()
        self.refresh_draft_view()

        self.statusBar().showMessage(
            f"New draft started from Slot {draft_slot}.",
            5000,
        )

    def resume_saved_draft(self) -> None:
        try:
            saved_data = self.store.load()

            self.simulations = saved_data[
                "simulations"
            ]

            self.session = LiveDraftSession(
                user_team_number=saved_data[
                    "draft_slot"
                ],
                completed_player_names=saved_data[
                    "drafted_player_names"
                ],
            )

        except (
            FileNotFoundError,
            ValueError,
        ) as error:
            QMessageBox.critical(
                self,
                "Could not resume draft",
                str(error),
            )

            return

        self.slot_selector.setCurrentText(
            str(
                self.session.user_team_number
            )
        )

        self.simulations_selector.setValue(
            self.simulations
        )

        self.clear_recommendations()
        self.refresh_draft_view()

        self.statusBar().showMessage(
            (
                f"Saved draft restored at "
                f"Pick {self.session.current_pick}."
            ),
            5000,
        )

    def delete_saved_draft(self) -> None:
        if not self.store.exists():
            return

        choice = QMessageBox.question(
            self,
            "Delete saved draft?",
            "This permanently deletes the saved live draft.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if choice != QMessageBox.StandardButton.Yes:
            return

        self.store.delete()
        self.show_start_screen()

        self.statusBar().showMessage(
            "Saved draft deleted.",
            5000,
        )

    def save_active_session(self) -> None:
        if self.session is None:
            return

        self.store.save(
            draft_slot=self.session.user_team_number,
            simulations=self.simulations,
            drafted_player_names=(
                self.session.completed_player_names
            ),
        )

    def refresh_draft_view(self) -> None:
        if self.session is None:
            self.show_start_screen()
            return

        if self.session.is_complete:
            self.status_label.setText(
                "DRAFT COMPLETE"
            )

            self.record_pick_button.setEnabled(
                False
            )

            self.analyze_button.setEnabled(
                False
            )

            self.store.delete()

        else:
            current_pick = self.session.current_pick

            current_round = (
                (current_pick - 1)
                // self.session.league.num_teams
            ) + 1

            turn_text = (
                "YOUR PICK"
                if self.session.is_user_turn
                else (
                    f"TEAM "
                    f"{self.session.current_team_number}"
                )
            )

            self.status_label.setText(
                (
                    f"ROUND {current_round}  •  "
                    f"OVERALL PICK {current_pick}  •  "
                    f"{turn_text}"
                )
            )

        self.war_room_header.update_state(self.session)
        self.draft_pulse_widget.update_from_session(self.session)
        self.refresh_available_players()
        self.refresh_roster()
        self.refresh_draft_board_dialog()

        self.draft_board_button.setEnabled(
            True
        )

        self.undo_button.setEnabled(
            bool(
                self.session.draft_results
            )
        )

        self.resume_button.setEnabled(
            self.store.exists()
        )

        self.delete_save_button.setEnabled(
            self.store.exists()
        )

    def refresh_available_players(self) -> None:
        # QListWidgetItem rows are intentionally lightweight. Avoiding
        # setItemWidget() keeps scrolling, filtering, and selection responsive.
        self.available_list.setUpdatesEnabled(False)
        self.available_list.blockSignals(True)

        try:
            self.available_list.clear()

            if self.session is None:
                return

            search_text = normalize_name(self.search_input.text())
            position_filter = self.position_filter.currentText()

            position_colors = {
                "QB": "#c084fc",
                "RB": "#6ee7b7",
                "WR": "#7dd3fc",
                "TE": "#fdba74",
                "DST": "#cbd5e1",
                "K": "#fde047",
            }

            for player in self.session.available_players():
                normalized_name = normalize_name(player.name)

                if search_text and search_text not in normalized_name:
                    continue

                player_position = player.position.upper()
                if (
                    position_filter != "ALL"
                    and not player_position.startswith(position_filter)
                ):
                    continue

                is_my_guy = normalized_name in self.approved_players
                base_position = player.position.upper().split("/")[0]

                # The icon occupies a permanent status column, while the
                # fixed-width font keeps rank, position, and name aligned.
                row_text = (
                    f"{player.rank:>3}  "
                    f"{player.position:<4}  "
                    f"{player.name}"
                )
                item = QListWidgetItem(
                    self.my_guy_icon if is_my_guy else self.normal_player_icon,
                    row_text,
                )
                item.setFont(self.available_player_font)
                item.setForeground(
                    QColor(position_colors.get(base_position, "#e2e8f0"))
                )
                item.setData(Qt.ItemDataRole.UserRole, player.name)
                item.setSizeHint(QSize(0, 39))

                tooltip = (
                    f"{base_position} • {player.team} • "
                    f"FantasyPros Rank {player.rank}"
                )
                if is_my_guy:
                    tooltip += " • My Guy"
                item.setToolTip(tooltip)

                self.available_list.addItem(item)
        finally:
            self.available_list.blockSignals(False)
            self.available_list.setUpdatesEnabled(True)
            self.available_list.viewport().update()
            self.update_selected_players()

    def refresh_roster(self) -> None:
        self.roster_list.clear()

        if self.session is None:
            self.roster_summary_label.setText(
                "No active draft."
            )

            return

        team = self.session.state.user_team

        for player in team.players:
            is_my_guy = (
                normalize_name(player.name)
                in self.approved_players
            )

            star = (
                "★ "
                if is_my_guy
                else ""
            )

            item = QListWidgetItem(
                (
                    f"{star}"
                    f"{player.position:<4} | "
                    f"{player.name}"
                )
            )

            position_colors = {
                "QB": "#c084fc",
                "RB": "#6ee7b7",
                "WR": "#7dd3fc",
                "TE": "#fdba74",
                "DST": "#cbd5e1",
                "K": "#fde047",
            }
            base_position = player.position.upper().split("/")[0]
            item.setForeground(QColor(position_colors.get(base_position, "#e2e8f0")))
            if is_my_guy:
                item.setBackground(QColor("#203428"))
                item.setToolTip("My Guy")

            self.roster_list.addItem(
                item
            )

        self.roster_summary_label.setText(
            (
                f"Players: {len(team.players)}/16\n"
                f"QB {team.count_position('QB')}  |  "
                f"RB {team.count_position('RB')}  |  "
                f"WR {team.count_position('WR')}\n"
                f"TE {team.count_position('TE')}  |  "
                f"DST {team.count_position('DST')}  |  "
                f"K {team.count_position('K')}"
            )
        )

    def update_selected_players(self) -> None:
        selected_count = len(
            self.available_list.selectedItems()
        )

        self.selected_player_label.setText(
            f"Selected candidates: {selected_count}"
        )

        has_selection = (
            selected_count > 0
        )

        self.record_pick_button.setEnabled(
            has_selection
        )

        can_analyze = (
            has_selection
            and self.session is not None
            and self.session.is_user_turn
            and self.session.next_user_pick is not None
        )

        self.analyze_button.setEnabled(
            can_analyze
        )

    def selected_player_names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            item.data(
                Qt.ItemDataRole.UserRole
            )
            for item in self.available_list.selectedItems()
        )

    def record_double_clicked_player(
        self,
        item: QListWidgetItem,
    ) -> None:
        if self.session is None:
            return

        player_name = item.data(
            Qt.ItemDataRole.UserRole
        )

        self.record_player_name(
            player_name
        )

    def record_selected_player(self) -> None:
        selected_names = (
            self.selected_player_names()
        )

        if not selected_names:
            return

        if len(selected_names) > 1:
            QMessageBox.warning(
                self,
                "Select one player",
                (
                    "Select exactly one player "
                    "when recording a pick."
                ),
            )

            return

        self.record_player_name(
            selected_names[0]
        )

    def record_player_name(
        self,
        player_name: str,
    ) -> None:
        if self.session is None:
            return

        team_number = (
            self.session.current_team_number
        )

        choice = QMessageBox.question(
            self,
            "Record draft pick?",
            (
                f"Record {player_name} for "
                f"Team {team_number} at "
                f"Pick {self.session.current_pick}?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if choice != QMessageBox.StandardButton.Yes:
            return

        try:
            draft_pick = self.session.record_pick(
                player_name
            )

        except (
            ValueError,
            RuntimeError,
        ) as error:
            QMessageBox.warning(
                self,
                "Could not record pick",
                str(error),
            )

            return

        self.save_active_session()
        self.clear_recommendations()
        self.refresh_draft_view()

        self.statusBar().showMessage(
            (
                f"Pick {draft_pick.overall}: "
                f"{draft_pick.player.name} "
                f"recorded for "
                f"Team {draft_pick.team_number}."
            ),
            6000,
        )

    def undo_last_pick(self) -> None:
        if (
            self.session is None
            or not self.session.draft_results
        ):
            return

        completed_names = list(
            self.session.completed_player_names
        )

        removed_player = (
            completed_names.pop()
        )

        self.session = LiveDraftSession(
            user_team_number=(
                self.session.user_team_number
            ),
            completed_player_names=tuple(
                completed_names
            ),
        )

        self.save_active_session()
        self.clear_recommendations()
        self.refresh_draft_view()

        self.statusBar().showMessage(
            f"Undid the selection of {removed_player}.",
            6000,
        )

    def analyze_selected_players(self) -> None:
        if self.session is None:
            return

        if not self.session.is_user_turn:
            QMessageBox.information(
                self,
                "Not your turn",
                (
                    "Recommendations are available "
                    "when your team is on the clock."
                ),
            )

            return

        next_pick = (
            self.session.next_user_pick
        )

        if next_pick is None:
            QMessageBox.information(
                self,
                "Final pick",
                (
                    "This is your final selection, "
                    "so wait analysis is unavailable."
                ),
            )

            return

        candidate_names = (
            self.selected_player_names()
        )

        if not candidate_names:
            return

        self.simulations = (
            self.simulations_selector.value()
        )

        self.analyze_button.setEnabled(
            False
        )

        self.record_pick_button.setEnabled(
            False
        )

        self.command_center.set_running(
            simulations=self.simulations,
            player_count=len(candidate_names),
        )

        self.statusBar().showMessage(
            "Recommendation analysis running..."
        )

        self.recommendation_thread = QThread()

        self.recommendation_worker = RecommendationWorker(
            candidate_names=candidate_names,
            draft_slot=(
                self.session.user_team_number
            ),
            completed_player_names=(
                self.session.completed_player_names
            ),
            current_pick=(
                self.session.current_pick
            ),
            next_pick=next_pick,
            simulations=self.simulations,
            user_team=(
                self.session.state.user_team
            ),
            draft_picks=tuple(self.session.draft_results),
        )

        self.recommendation_worker.moveToThread(
            self.recommendation_thread
        )

        self.recommendation_thread.started.connect(
            self.recommendation_worker.run
        )

        self.recommendation_worker.finished.connect(
            self.handle_recommendations
        )

        self.recommendation_worker.failed.connect(
            self.handle_recommendation_error
        )

        self.recommendation_worker.finished.connect(
            self.recommendation_thread.quit
        )

        self.recommendation_worker.failed.connect(
            self.recommendation_thread.quit
        )

        self.recommendation_thread.finished.connect(
            self.cleanup_recommendation_thread
        )

        self.recommendation_thread.start()

    def handle_recommendations(
        self,
        recommendations,
        runtime: float,
    ) -> None:
        self.current_recommendations = list(
            recommendations
        )

        self.command_center.set_results(
            recommendations=recommendations,
            runtime=runtime,
        )

        self.statusBar().showMessage(
            (
                f"Analysis finished in "
                f"{runtime:.1f} seconds."
            ),
            6000,
        )

        self.update_selected_players()

    def apply_recommendation_color(
        self,
        item: QTableWidgetItem,
        column: int,
        grade: str,
        action: str,
    ) -> None:
        if column == 4:
            if grade in {
                "A+",
                "A",
            }:
                item.setForeground(
                    QColor(
                        "#4ade80"
                    )
                )

            elif grade in {
                "B+",
                "B",
            }:
                item.setForeground(
                    QColor(
                        "#facc15"
                    )
                )

            else:
                item.setForeground(
                    QColor(
                        "#fb7185"
                    )
                )

        if column == 6:
            if action == "DRAFT NOW":
                item.setForeground(
                    QColor(
                        "#4ade80"
                    )
                )

            elif action in {
                "RISKY TO WAIT",
                "CAN PROBABLY WAIT",
            }:
                item.setForeground(
                    QColor(
                        "#facc15"
                    )
                )

            else:
                item.setForeground(
                    QColor(
                        "#93c5fd"
                    )
                )

    def handle_recommendation_error(
        self,
        error_message: str,
    ) -> None:
        self.recommendation_status_label.setText(
            "Analysis failed."
        )

        QMessageBox.critical(
            self,
            "Recommendation error",
            error_message,
        )

        self.statusBar().showMessage(
            "Recommendation analysis failed.",
            6000,
        )

        self.update_selected_players()

    def cleanup_recommendation_thread(
        self,
    ) -> None:
        if self.recommendation_worker is not None:
            self.recommendation_worker.deleteLater()

        if self.recommendation_thread is not None:
            self.recommendation_thread.deleteLater()

        self.recommendation_worker = None
        self.recommendation_thread = None

    def show_selected_recommendation(
        self,
    ) -> None:
        selected_rows = (
            self.recommendation_table
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return

        row = selected_rows[0].row()

        player_item = (
            self.recommendation_table.item(
                row,
                1,
            )
        )

        if player_item is None:
            return

        player_name = (
            player_item.text()
        )

        recommendation = next(
            (
                item
                for item in self.current_recommendations
                if item.player_name == player_name
            ),
            None,
        )

        if recommendation is None:
            return

        self.command_center.display_recommendation(
            recommendation
        )

    def open_draft_board(self) -> None:
        if self.session is None:
            QMessageBox.information(
                self,
                "No active draft",
                (
                    "Start or resume a draft "
                    "before opening the draft board."
                ),
            )
            return

        if self.draft_board_dialog is None:
            self.draft_board_dialog = (
                DraftBoardDialog(self)
            )

        self.draft_board_dialog.refresh_board(
            session=self.session,
            approved_players=(
                self.approved_players
            ),
        )

        self.draft_board_dialog.show()
        self.draft_board_dialog.raise_()
        self.draft_board_dialog.activateWindow()

    def refresh_draft_board_dialog(
        self,
    ) -> None:
        if self.draft_board_dialog is None:
            return

        self.draft_board_dialog.refresh_board(
            session=self.session,
            approved_players=(
                self.approved_players
            ),
        )

    def clear_recommendations(self) -> None:
        self.current_recommendations = []
        self.command_center.reset()

    def closeEvent(self, event) -> None:
        self.save_active_session()

        if self.draft_board_dialog is not None:
            self.draft_board_dialog.close()

        if (
            self.recommendation_thread is not None
            and self.recommendation_thread.isRunning()
        ):
            self.recommendation_thread.quit()

            self.recommendation_thread.wait(
                3000
            )

        event.accept()


def main() -> None:
    application = QApplication(
        sys.argv
    )

    application.setStyleSheet(
        DARK_STYLESHEET
    )

    window = GridironWindow()

    window.show()

    sys.exit(
        application.exec()
    )
