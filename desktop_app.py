import sys
from time import perf_counter

from PySide6.QtCore import (
    QObject,
    QThread,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from draft_session_store import DraftSessionStore
from live_draft import LiveDraftSession
from preferences import load_my_guys, normalize_name
from projection_loader import load_projections
from recommendation_engine import RecommendationEngine
from wait_analyzer import WaitAnalyzer


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
        self.completed_player_names = (
            completed_player_names
        )
        self.current_pick = current_pick
        self.next_pick = next_pick
        self.simulations = simulations
        self.user_team = user_team

    def run(self) -> None:
        try:
            start_time = perf_counter()

            wait_analyzer = WaitAnalyzer()

            wait_results = (
                wait_analyzer.analyze_live_players(
                    player_names=self.candidate_names,
                    draft_slot=self.draft_slot,
                    completed_player_names=(
                        self.completed_player_names
                    ),
                    current_pick=self.current_pick,
                    next_pick=self.next_pick,
                    simulations=self.simulations,
                )
            )

            recommendation_engine = (
                RecommendationEngine(
                    players=wait_analyzer.players,
                    projections=load_projections(),
                    approved_players=(
                        wait_analyzer.approved_players
                    ),
                )
            )

            recommendations = (
                recommendation_engine.recommend(
                    wait_results=wait_results,
                    user_team=self.user_team,
                )
            )

            runtime = perf_counter() - start_time

            self.finished.emit(
                recommendations,
                runtime,
            )

        except Exception as error:
            self.failed.emit(
                str(error)
            )


class GridironWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "Gridiron AI"
        )

        self.resize(
            1450,
            850,
        )

        self.store = DraftSessionStore()

        self.session: LiveDraftSession | None = None
        self.simulations = DEFAULT_SIMULATIONS

        self.approved_players = load_my_guys()

        self.recommendation_thread: (
            QThread | None
        ) = None

        self.recommendation_worker: (
            RecommendationWorker | None
        ) = None

        self.setup_ui()
        self.show_start_screen()

    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(
            central_widget
        )

        self.main_layout = QVBoxLayout(
            central_widget
        )

        self.title_label = QLabel(
            "GRIDIRON AI"
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.title_label.setStyleSheet(
            """
            font-size: 30px;
            font-weight: bold;
            padding: 12px;
            """
        )

        self.main_layout.addWidget(
            self.title_label
        )

        self.status_label = QLabel()

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setStyleSheet(
            """
            font-size: 17px;
            font-weight: bold;
            padding: 8px;
            """
        )

        self.main_layout.addWidget(
            self.status_label
        )

        self.content_layout = QHBoxLayout()

        self.main_layout.addLayout(
            self.content_layout
        )

        self.left_panel = QVBoxLayout()
        self.middle_panel = QVBoxLayout()
        self.right_panel = QVBoxLayout()

        self.content_layout.addLayout(
            self.left_panel,
            1,
        )

        self.content_layout.addLayout(
            self.middle_panel,
            2,
        )

        self.content_layout.addLayout(
            self.right_panel,
            2,
        )

        self.setup_left_panel()
        self.setup_middle_panel()
        self.setup_right_panel()

    def setup_left_panel(self) -> None:
        heading = QLabel(
            "Draft Setup"
        )

        heading.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        self.left_panel.addWidget(
            heading
        )

        self.left_panel.addWidget(
            QLabel("Your draft slot")
        )

        self.slot_selector = QComboBox()

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

        self.new_draft_button.clicked.connect(
            self.start_new_draft
        )

        self.left_panel.addWidget(
            self.new_draft_button
        )

        self.resume_button = QPushButton(
            "Resume Saved Draft"
        )

        self.resume_button.clicked.connect(
            self.resume_saved_draft
        )

        self.left_panel.addWidget(
            self.resume_button
        )

        self.delete_save_button = QPushButton(
            "Delete Saved Draft"
        )

        self.delete_save_button.clicked.connect(
            self.delete_saved_draft
        )

        self.left_panel.addWidget(
            self.delete_save_button
        )

        self.left_panel.addSpacing(
            20
        )

        roster_heading = QLabel(
            "Your Roster"
        )

        roster_heading.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        self.left_panel.addWidget(
            roster_heading
        )

        self.roster_list = QListWidget()

        self.left_panel.addWidget(
            self.roster_list
        )

        self.roster_summary_label = QLabel()

        self.roster_summary_label.setWordWrap(
            True
        )

        self.left_panel.addWidget(
            self.roster_summary_label
        )

    def setup_middle_panel(self) -> None:
        heading = QLabel(
            "Available Players"
        )

        heading.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        self.middle_panel.addWidget(
            heading
        )

        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search player..."
        )

        self.search_input.textChanged.connect(
            self.refresh_available_players
        )

        filter_layout.addWidget(
            self.search_input
        )

        self.position_filter = QComboBox()

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

        self.available_list = QListWidget()

        self.available_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )

        self.available_list.itemSelectionChanged.connect(
            self.update_selected_players
        )

        self.middle_panel.addWidget(
            self.available_list
        )

        self.selected_player_label = QLabel(
            "Selected candidates: 0"
        )

        self.selected_player_label.setStyleSheet(
            """
            font-size: 15px;
            padding: 8px;
            """
        )

        self.middle_panel.addWidget(
            self.selected_player_label
        )

        self.button_layout = QHBoxLayout()

        self.record_pick_button = QPushButton(
            "Record Pick"
        )

        self.record_pick_button.clicked.connect(
            self.record_selected_player
        )

        self.record_pick_button.setEnabled(
            False
        )

        self.button_layout.addWidget(
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

        self.button_layout.addWidget(
            self.analyze_button
        )

        self.middle_panel.addLayout(
            self.button_layout
        )

        legend = QLabel(
            "★ = My Guy"
        )

        legend.setStyleSheet(
            """
            font-weight: bold;
            padding: 4px;
            """
        )

        self.middle_panel.addWidget(
            legend
        )

    def setup_right_panel(self) -> None:
        heading = QLabel(
            "Recommendations"
        )

        heading.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            """
        )

        self.right_panel.addWidget(
            heading
        )

        self.recommendation_status_label = QLabel(
            "Select players and click "
            "Analyze Selected."
        )

        self.recommendation_status_label.setWordWrap(
            True
        )

        self.right_panel.addWidget(
            self.recommendation_status_label
        )

        self.recommendation_table = QTableWidget(
            0,
            7,
        )

        self.recommendation_table.setHorizontalHeaderLabels(
            (
                "Rank",
                "Player",
                "Pos",
                "Score",
                "Grade",
                "Survives",
                "Action",
            )
        )

        self.recommendation_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.recommendation_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.recommendation_table.itemSelectionChanged.connect(
            self.show_selected_recommendation
        )

        self.recommendation_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.right_panel.addWidget(
            self.recommendation_table
        )

        self.top_pick_label = QLabel(
            "Top pick: None"
        )

        self.top_pick_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            padding: 8px;
            """
        )

        self.right_panel.addWidget(
            self.top_pick_label
        )

        self.reason_label = QLabel(
            "Recommendation details will "
            "appear here."
        )

        self.reason_label.setWordWrap(
            True
        )

        self.reason_label.setStyleSheet(
            """
            padding: 10px;
            border: 1px solid gray;
            """
        )

        self.right_panel.addWidget(
            self.reason_label
        )

        self.current_recommendations = []

    def show_start_screen(self) -> None:
        self.session = None

        self.status_label.setText(
            "Start a new draft or resume "
            "a saved session."
        )

        self.available_list.clear()
        self.roster_list.clear()
        self.recommendation_table.setRowCount(
            0
        )

        self.selected_player_label.setText(
            "Selected candidates: 0"
        )

        self.roster_summary_label.setText(
            "No active draft."
        )

        self.top_pick_label.setText(
            "Top pick: None"
        )

        self.reason_label.setText(
            "Recommendation details will "
            "appear here."
        )

        self.record_pick_button.setEnabled(
            False
        )

        self.analyze_button.setEnabled(
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

            if (
                choice
                != QMessageBox.StandardButton.Yes
            ):
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

        self.save_active_session()
        self.refresh_draft_view()

    def resume_saved_draft(self) -> None:
        try:
            saved_data = self.store.load()

            self.simulations = saved_data[
                "simulations"
            ]

            self.session = LiveDraftSession(
                user_team_number=(
                    saved_data["draft_slot"]
                ),
                completed_player_names=(
                    saved_data[
                        "drafted_player_names"
                    ]
                ),
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

        self.refresh_draft_view()

    def delete_saved_draft(self) -> None:
        if not self.store.exists():
            return

        choice = QMessageBox.question(
            self,
            "Delete saved draft?",
            (
                "This permanently deletes "
                "the saved live draft."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            choice
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.store.delete()
        self.show_start_screen()

    def save_active_session(self) -> None:
        if self.session is None:
            return

        self.store.save(
            draft_slot=(
                self.session.user_team_number
            ),
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
                "Draft complete."
            )

            self.record_pick_button.setEnabled(
                False
            )

            self.analyze_button.setEnabled(
                False
            )

            self.store.delete()

        else:
            turn_text = (
                "YOUR PICK"
                if self.session.is_user_turn
                else (
                    f"Team "
                    f"{self.session.current_team_number}"
                )
            )

            self.status_label.setText(
                (
                    f"Overall Pick "
                    f"{self.session.current_pick} "
                    f"— {turn_text}"
                )
            )

        self.refresh_available_players()
        self.refresh_roster()

        self.resume_button.setEnabled(
            self.store.exists()
        )

        self.delete_save_button.setEnabled(
            self.store.exists()
        )

    def refresh_available_players(self) -> None:
        self.available_list.clear()

        if self.session is None:
            return

        search_text = normalize_name(
            self.search_input.text()
        )

        position_filter = (
            self.position_filter.currentText()
        )

        for player in (
            self.session.available_players()
        ):
            normalized_name = normalize_name(
                player.name
            )

            if (
                search_text
                and search_text not in normalized_name
            ):
                continue

            player_position = (
                player.position.upper()
            )

            if (
                position_filter != "ALL"
                and not player_position.startswith(
                    position_filter
                )
            ):
                continue

            is_my_guy = (
                normalized_name
                in self.approved_players
            )

            star = "★ " if is_my_guy else ""

            item = QListWidgetItem(
                (
                    f"{star}"
                    f"{player.rank:>3} | "
                    f"{player.position:<4} | "
                    f"{player.name}"
                )
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                player.name,
            )

            if is_my_guy:
                item.setBackground(
                    QColor(
                        205,
                        245,
                        210,
                    )
                )

                item.setToolTip(
                    "My Guy"
                )

            self.available_list.addItem(
                item
            )

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

            star = "★ " if is_my_guy else ""

            self.roster_list.addItem(
                (
                    f"{star}"
                    f"{player.position:<4} | "
                    f"{player.name}"
                )
            )

        self.roster_summary_label.setText(
            (
                f"Players: "
                f"{len(team.players)}/16\n"
                f"QB: "
                f"{team.count_position('QB')} | "
                f"RB: "
                f"{team.count_position('RB')} | "
                f"WR: "
                f"{team.count_position('WR')} | "
                f"TE: "
                f"{team.count_position('TE')} | "
                f"DST: "
                f"{team.count_position('DST')} | "
                f"K: "
                f"{team.count_position('K')}"
            )
        )

    def update_selected_players(self) -> None:
        selected_count = len(
            self.available_list.selectedItems()
        )

        self.selected_player_label.setText(
            f"Selected candidates: "
            f"{selected_count}"
        )

        has_selection = selected_count > 0

        self.record_pick_button.setEnabled(
            has_selection
        )

        can_analyze = (
            has_selection
            and self.session is not None
            and self.session.is_user_turn
            and self.session.next_user_pick
            is not None
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
            for item in (
                self.available_list.selectedItems()
            )
        )

    def record_selected_player(self) -> None:
        if self.session is None:
            return

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

        player_name = selected_names[0]

        try:
            draft_pick = (
                self.session.record_pick(
                    player_name
                )
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

        self.recommendation_table.setRowCount(
            0
        )

        self.current_recommendations = []

        QMessageBox.information(
            self,
            "Pick recorded",
            (
                f"Pick {draft_pick.overall}: "
                f"{draft_pick.player.name}\n"
                f"Team {draft_pick.team_number}"
            ),
        )

        self.refresh_draft_view()

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

        self.recommendation_status_label.setText(
            (
                f"Running {self.simulations} "
                f"simulations for "
                f"{len(candidate_names)} players..."
            )
        )

        self.recommendation_thread = QThread()

        self.recommendation_worker = (
            RecommendationWorker(
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
            )
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

        self.recommendation_table.setRowCount(
            len(recommendations)
        )

        for row, recommendation in enumerate(
            recommendations
        ):
            survival_text = (
                f"{recommendation.survival_probability:.1%}"
                if recommendation.survival_probability
                is not None
                else "N/A"
            )

            values = (
                str(row + 1),
                recommendation.player_name,
                recommendation.position,
                f"{recommendation.score:.1f}",
                recommendation.grade,
                survival_text,
                recommendation.action,
            )

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    value
                )

                self.recommendation_table.setItem(
                    row,
                    column,
                    item,
                )

        self.recommendation_table.resizeColumnsToContents()

        self.recommendation_status_label.setText(
            f"Analysis completed in "
            f"{runtime:.1f} seconds."
        )

        if recommendations:
            top = recommendations[0]

            self.top_pick_label.setText(
                (
                    f"Top pick: "
                    f"{top.player_name} "
                    f"({top.position}) — "
                    f"{top.grade}"
                )
            )

            self.reason_label.setText(
                "\n".join(
                    f"• {reason}"
                    for reason in top.reasons
                )
            )

            self.recommendation_table.selectRow(
                0
            )

        self.update_selected_players()

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
            self.recommendation_table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return

        row = selected_rows[0].row()

        if not (
            0
            <= row
            < len(self.current_recommendations)
        ):
            return

        recommendation = (
            self.current_recommendations[row]
        )

        self.top_pick_label.setText(
            (
                f"{recommendation.player_name} "
                f"({recommendation.position}) — "
                f"{recommendation.grade} | "
                f"{recommendation.action}"
            )
        )

        self.reason_label.setText(
            "\n".join(
                f"• {reason}"
                for reason
                in recommendation.reasons
            )
        )

    def closeEvent(self, event) -> None:
        self.save_active_session()

        if (
            self.recommendation_thread
            is not None
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

    window = GridironWindow()
    window.show()

    sys.exit(
        application.exec()
    )


if __name__ == "__main__":
    main()