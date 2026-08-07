from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QHeaderView, QLabel, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from live_draft import LiveDraftSession
from preferences import normalize_name


class DraftBoardDialog(QDialog):
    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            "Gridiron AI — Draft Board"
        )

        self.resize(
            1450,
            760,
        )

        self.setMinimumSize(
            1000,
            560,
        )

        layout = QVBoxLayout(self)

        self.heading_label = QLabel(
            "VISUAL DRAFT BOARD"
        )

        self.heading_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.heading_label.setStyleSheet(
            "font-size: 22px; "
            "font-weight: 800; "
            "padding: 8px;"
        )

        layout.addWidget(
            self.heading_label
        )

        self.summary_label = QLabel(
            "No active draft."
        )

        self.summary_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.summary_label.setStyleSheet(
            "color: #cbd5e1; "
            "padding-bottom: 8px;"
        )

        layout.addWidget(
            self.summary_label
        )

        self.table = QTableWidget(
            16,
            10,
        )

        self.table.setHorizontalHeaderLabels(
            tuple(
                f"Team {team_number}"
                for team_number in range(1, 11)
            )
        )

        self.table.setVerticalHeaderLabels(
            tuple(
                f"Round {round_number}"
                for round_number in range(1, 17)
            )
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setWordWrap(
            True
        )

        horizontal_header = (
            self.table.horizontalHeader()
        )

        for column in range(10):
            horizontal_header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.Stretch,
            )

        vertical_header = (
            self.table.verticalHeader()
        )

        vertical_header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        layout.addWidget(
            self.table
        )

        self.legend_label = QLabel(
            "Blue border = your team   •   "
            "Green = My Guy   •   "
            "Gold = current pick"
        )

        self.legend_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.legend_label.setStyleSheet(
            "padding: 8px; "
            "font-weight: 700;"
        )

        layout.addWidget(
            self.legend_label
        )

    def refresh_board(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
    ) -> None:
        self.table.clearContents()

        if session is None:
            self.summary_label.setText(
                "No active draft."
            )
            return

        self.summary_label.setText(
            f"Completed picks: "
            f"{len(session.draft_results)}/160  •  "
            f"Next pick: {session.current_pick}  •  "
            f"Your slot: {session.user_team_number}"
        )

        picks_by_overall = {
            draft_pick.overall: draft_pick
            for draft_pick in session.draft_results
        }

        for overall_pick, team_number in enumerate(
            session.league.draft_order,
            start=1,
        ):
            round_number = (
                (overall_pick - 1)
                // session.league.num_teams
            ) + 1

            row = round_number - 1
            column = team_number - 1

            draft_pick = picks_by_overall.get(
                overall_pick
            )

            if draft_pick is None:
                text = f"#{overall_pick}"
            else:
                player = draft_pick.player
                text = (
                    f"#{overall_pick}  "
                    f"{player.position}\n"
                    f"{player.name}"
                )

            item = QTableWidgetItem(text)

            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            tooltip_parts = [
                f"Overall Pick {overall_pick}",
                f"Team {team_number}",
                f"Round {round_number}",
            ]

            if draft_pick is not None:
                tooltip_parts.append(
                    draft_pick.player.name
                )

            item.setToolTip(
                " | ".join(tooltip_parts)
            )

            styles: list[str] = []

            if (
                team_number
                == session.user_team_number
            ):
                styles.extend(
                    (
                        "border: 2px solid #3b82f6;",
                        "font-weight: 700;",
                    )
                )

            if (
                draft_pick is not None
                and normalize_name(
                    draft_pick.player.name
                ) in approved_players
            ):
                item.setForeground(
                    QColor("#86efac")
                )

            if overall_pick == session.current_pick:
                item.setBackground(
                    QColor("#7c5c00")
                )
                styles.append(
                    "font-weight: 800;"
                )

            if styles:
                item.setData(
                    Qt.ItemDataRole.UserRole + 1,
                    " ".join(styles),
                )

            self.table.setItem(
                row,
                column,
                item,
            )

        self.highlight_user_team(
            session.user_team_number
        )

        self.table.resizeRowsToContents()

    def highlight_user_team(
        self,
        user_team_number: int,
    ) -> None:
        user_column = user_team_number - 1

        for row in range(
            self.table.rowCount()
        ):
            item = self.table.item(
                row,
                user_column,
            )

            if item is None:
                continue

            font = item.font()
            font.setBold(True)
            item.setFont(font)

            if item.background().color().name() == "#000000":
                item.setBackground(
                    QColor("#172554")
                )
