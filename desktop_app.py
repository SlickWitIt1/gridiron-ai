import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from draft_session_store import DraftSessionStore
from live_draft import LiveDraftSession


DEFAULT_SIMULATIONS = 100


class GridironWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Gridiron AI")
        self.resize(1100, 720)

        self.store = DraftSessionStore()

        self.session: LiveDraftSession | None = None
        self.simulations = DEFAULT_SIMULATIONS

        self.setup_ui()
        self.show_start_screen()

    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

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
            "font-size: 28px; "
            "font-weight: bold; "
            "padding: 12px;"
        )

        self.main_layout.addWidget(
            self.title_label
        )

        self.status_label = QLabel()

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setStyleSheet(
            "font-size: 16px; "
            "padding: 8px;"
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
            1,
        )

        self.setup_left_panel()
        self.setup_middle_panel()
        self.setup_right_panel()

    def setup_left_panel(self) -> None:
        heading = QLabel(
            "Draft Setup"
        )

        heading.setStyleSheet(
            "font-size: 18px; "
            "font-weight: bold;"
        )

        self.left_panel.addWidget(
            heading
        )

        slot_label = QLabel(
            "Your draft slot"
        )

        self.left_panel.addWidget(
            slot_label
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

        simulations_label = QLabel(
            "Simulations per candidate"
        )

        self.left_panel.addWidget(
            simulations_label
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

        self.left_panel.addStretch()

    def setup_middle_panel(self) -> None:
        heading = QLabel(
            "Available Players"
        )

        heading.setStyleSheet(
            "font-size: 18px; "
            "font-weight: bold;"
        )

        self.middle_panel.addWidget(
            heading
        )

        self.available_list = QListWidget()

        self.available_list.itemSelectionChanged.connect(
            self.update_selected_player
        )

        self.middle_panel.addWidget(
            self.available_list
        )

        self.selected_player_label = QLabel(
            "Selected player: None"
        )

        self.selected_player_label.setStyleSheet(
            "font-size: 15px; "
            "padding: 8px;"
        )

        self.middle_panel.addWidget(
            self.selected_player_label
        )

        self.record_pick_button = QPushButton(
            "Record Selected Player"
        )

        self.record_pick_button.clicked.connect(
            self.record_selected_player
        )

        self.record_pick_button.setEnabled(
            False
        )

        self.middle_panel.addWidget(
            self.record_pick_button
        )

    def setup_right_panel(self) -> None:
        heading = QLabel(
            "Your Roster"
        )

        heading.setStyleSheet(
            "font-size: 18px; "
            "font-weight: bold;"
        )

        self.right_panel.addWidget(
            heading
        )

        self.roster_list = QListWidget()

        self.right_panel.addWidget(
            self.roster_list
        )

        self.roster_summary_label = QLabel()

        self.roster_summary_label.setWordWrap(
            True
        )

        self.roster_summary_label.setStyleSheet(
            "padding: 8px;"
        )

        self.right_panel.addWidget(
            self.roster_summary_label
        )

    def show_start_screen(self) -> None:
        self.session = None

        self.status_label.setText(
            "Start a new draft or resume "
            "a saved session."
        )

        self.available_list.clear()
        self.roster_list.clear()

        self.selected_player_label.setText(
            "Selected player: None"
        )

        self.roster_summary_label.setText(
            "No active draft."
        )

        self.record_pick_button.setEnabled(
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

        for player in (
            self.session.available_players()
        ):
            item = QListWidgetItem(
                (
                    f"{player.rank:>3} | "
                    f"{player.position:<4} | "
                    f"{player.name}"
                )
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                player.name,
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
            self.roster_list.addItem(
                (
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

    def update_selected_player(self) -> None:
        selected_items = (
            self.available_list.selectedItems()
        )

        if not selected_items:
            self.selected_player_label.setText(
                "Selected player: None"
            )

            self.record_pick_button.setEnabled(
                False
            )

            return

        player_name = selected_items[0].data(
            Qt.ItemDataRole.UserRole
        )

        self.selected_player_label.setText(
            f"Selected player: {player_name}"
        )

        self.record_pick_button.setEnabled(
            True
        )

    def record_selected_player(self) -> None:
        if self.session is None:
            return

        selected_items = (
            self.available_list.selectedItems()
        )

        if not selected_items:
            return

        player_name = selected_items[0].data(
            Qt.ItemDataRole.UserRole
        )

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

    def closeEvent(self, event) -> None:
        self.save_active_session()
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