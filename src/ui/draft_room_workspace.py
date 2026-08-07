from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from live_draft import LiveDraftSession
from preferences import normalize_name
from projection_loader import load_projections
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


class DraftRoomPlayerBrowser(QFrame):
    """Sleeper-inspired compact browser for recording picks and selecting AI candidates."""

    record_requested = Signal(str)
    analyze_requested = Signal(object)
    undo_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DraftRoomPlayerBrowser")

        self._session: LiveDraftSession | None = None
        self._approved_players: set[str] = set()
        self._projections = load_projections()

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(0)
        title = QLabel("AVAILABLE PLAYERS")
        title.setObjectName("WorkspaceTitle")
        self.context_label = QLabel("Select the player drafted.")
        self.context_label.setObjectName("WorkspaceSubtle")
        title_stack.addWidget(title)
        title_stack.addWidget(self.context_label)
        top.addLayout(title_stack)

        top.addStretch(1)

        self.search = QLineEdit()
        self.search.setObjectName("WorkspaceSearch")
        self.search.setPlaceholderText("Find player…")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(210)
        self.search.textChanged.connect(self.refresh_table)
        top.addWidget(self.search)

        self.position_filter = QComboBox()
        self.position_filter.setObjectName("WorkspaceFilter")
        self.position_filter.addItems(POSITION_FILTERS)
        self.position_filter.setFixedWidth(78)
        self.position_filter.currentTextChanged.connect(self.refresh_table)
        top.addWidget(self.position_filter)

        layout.addLayout(top)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("DraftRoomPlayerTable")
        self.table.setHorizontalHeaderLabels(
            ("RK", "PLAYER", "POS", "TEAM", "BYE", "PROJ", "TIER")
        )
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.setWordWrap(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in (2, 3, 4, 5, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setColumnWidth(0, 48)
        self.table.setColumnWidth(2, 55)
        self.table.setColumnWidth(3, 55)
        self.table.setColumnWidth(4, 48)
        self.table.setColumnWidth(5, 74)
        self.table.setColumnWidth(6, 50)

        self.table.itemSelectionChanged.connect(self._update_action_state)
        self.table.itemDoubleClicked.connect(self._double_click)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.selection_label = QLabel("No player selected")
        self.selection_label.setObjectName("WorkspaceSelection")
        actions.addWidget(self.selection_label, 1)

        self.undo_button = QPushButton("UNDO")
        self.undo_button.setObjectName("WorkspaceSecondaryButton")
        self.undo_button.setFixedHeight(34)
        self.undo_button.clicked.connect(self.undo_requested.emit)
        actions.addWidget(self.undo_button)

        self.analyze_button = QPushButton("ANALYZE SELECTED")
        self.analyze_button.setObjectName("WorkspaceAnalyzeButton")
        self.analyze_button.setFixedHeight(34)
        self.analyze_button.clicked.connect(self._analyze)
        actions.addWidget(self.analyze_button)

        self.record_button = QPushButton("RECORD PICK")
        self.record_button.setObjectName("WorkspacePrimaryButton")
        self.record_button.setFixedHeight(34)
        self.record_button.clicked.connect(self._record)
        actions.addWidget(self.record_button)

        layout.addLayout(actions)

    def refresh(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
    ) -> None:
        self._session = session
        self._approved_players = set(approved_players)

        if session is None:
            self.context_label.setText("No active draft.")
        elif session.is_complete:
            self.context_label.setText("Draft complete.")
        elif session.is_user_turn:
            self.context_label.setText(
                f"YOU'RE ON THE CLOCK • PICK {session.current_pick} • "
                "Select candidates to analyze or record your pick."
            )
        else:
            self.context_label.setText(
                f"TEAM {session.current_team_number} ON CLOCK • PICK {session.current_pick} • "
                "Double-click the player they drafted."
            )

        self.undo_button.setEnabled(
            session is not None and bool(session.draft_results)
        )
        self.refresh_table()

    def selected_player_names(self) -> tuple[str, ...]:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        names = []
        for row in rows:
            item = self.table.item(row, 1)
            if item is None:
                continue
            value = item.data(Qt.ItemDataRole.UserRole)
            if value:
                names.append(str(value))
        return tuple(names)

    def refresh_table(self) -> None:
        previously_selected = set(self.selected_player_names())

        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        try:
            if self._session is None:
                return

            query = normalize_name(self.search.text())
            wanted_position = self.position_filter.currentText().upper()

            for player in self._session.available_players():
                position = base_position(player.position).upper()

                if wanted_position != "ALL" and position != wanted_position:
                    continue
                if query and query not in normalize_name(player.name):
                    continue

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setRowHeight(row, 30)

                projection = self._projections.get(normalize_name(player.name))
                projected_points = getattr(projection, "fantasy_points", None)

                values = (
                    str(getattr(player, "rank", "") or ""),
                    player.name,
                    player.position,
                    player.team,
                    str(getattr(player, "bye", "") or "—"),
                    f"{projected_points:.1f}" if isinstance(projected_points, (int, float)) else "—",
                    str(getattr(player, "tier", "") or "—"),
                )

                for column, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, player.name)

                    if column == 1:
                        is_my_guy = normalize_name(player.name) in self._approved_players
                        if is_my_guy:
                            item.setText(f"{player.name}   ★")
                            item.setForeground(QColor("#fde047"))
                    elif column == 2:
                        item.setForeground(
                            QColor(POSITION_COLORS.get(position, "#e2e8f0"))
                        )

                    if column != 1:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.table.setItem(row, column, item)

                if player.name in previously_selected:
                    self.table.selectRow(row)
        finally:
            self.table.blockSignals(False)
            self.table.setUpdatesEnabled(True)

        self._update_action_state()

    def _update_action_state(self) -> None:
        names = self.selected_player_names()
        count = len(names)
        is_user_turn = bool(self._session and self._session.is_user_turn)
        can_record = bool(self._session and not self._session.is_complete and count == 1)

        self.record_button.setEnabled(can_record)
        self.analyze_button.setEnabled(is_user_turn and count >= 1)

        if count == 0:
            self.selection_label.setText("No player selected")
            self.record_button.setText("RECORD PICK")
        elif count == 1:
            self.selection_label.setText(names[0])
            self.record_button.setText("RECORD PICK")
        else:
            self.selection_label.setText(f"{count} candidates selected")

    def _record(self) -> None:
        names = self.selected_player_names()
        if len(names) == 1:
            self.record_requested.emit(names[0])

    def _analyze(self) -> None:
        names = self.selected_player_names()
        if names:
            self.analyze_requested.emit(names)

    def _double_click(self, item: QTableWidgetItem) -> None:
        value = item.data(Qt.ItemDataRole.UserRole)
        if value:
            self.record_requested.emit(str(value))


class DraftRoomAnalyticsPanel(QFrame):
    """Compact Gridiron AI decision surface for the unified Draft Room."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DraftRoomAnalyticsPanel")
        self._build_ui()
        self.reset()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        eyebrow = QLabel("GRIDIRON AI")
        eyebrow.setObjectName("AnalyticsEyebrow")
        layout.addWidget(eyebrow)

        self.player_label = QLabel("Ready when you are")
        self.player_label.setObjectName("AnalyticsPlayer")
        self.player_label.setWordWrap(False)
        layout.addWidget(self.player_label)

        self.meta_label = QLabel("Select candidates and run an analysis.")
        self.meta_label.setObjectName("AnalyticsMeta")
        self.meta_label.setWordWrap(True)
        layout.addWidget(self.meta_label)

        metrics = QGridLayout()
        metrics.setSpacing(7)

        self.score_card = self._metric_card("DECISION SCORE")
        self.survival_card = self._metric_card("SURVIVES")
        self.cost_card = self._metric_card("COST TO WAIT")
        self.fit_card = self._metric_card("ROSTER FIT")

        metrics.addWidget(self.score_card, 0, 0)
        metrics.addWidget(self.survival_card, 0, 1)
        metrics.addWidget(self.cost_card, 1, 0)
        metrics.addWidget(self.fit_card, 1, 1)
        layout.addLayout(metrics)

        self.action_label = QLabel("ANALYZE PLAYERS")
        self.action_label.setObjectName("AnalyticsAction")
        self.action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.action_label)

        reasons_title = QLabel("WHY THIS PICK")
        reasons_title.setObjectName("AnalyticsSectionTitle")
        layout.addWidget(reasons_title)

        self.reasons_label = QLabel(
            "Your top recommendation and the strongest reasons will appear here."
        )
        self.reasons_label.setObjectName("AnalyticsReasons")
        self.reasons_label.setWordWrap(True)
        layout.addWidget(self.reasons_label, 1)

        self.alt_label = QLabel("")
        self.alt_label.setObjectName("AnalyticsAlternatives")
        self.alt_label.setWordWrap(True)
        layout.addWidget(self.alt_label)

    @staticmethod
    def _metric_card(title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("AnalyticsMetricCard")
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(9, 7, 9, 7)
        card_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("AnalyticsMetricTitle")
        value_label = QLabel("—")
        value_label.setObjectName("AnalyticsMetricValue")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        frame.value_label = value_label
        return frame

    def reset(self) -> None:
        self.player_label.setText("Ready when you are")
        self.meta_label.setText("Select candidates and run an analysis.")
        self.score_card.value_label.setText("—")
        self.survival_card.value_label.setText("—")
        self.cost_card.value_label.setText("—")
        self.fit_card.value_label.setText("—")
        self.action_label.setText("ANALYZE PLAYERS")
        self.action_label.setProperty("action", "neutral")
        self._refresh(self.action_label)
        self.reasons_label.setText(
            "Your top recommendation and the strongest reasons will appear here."
        )
        self.alt_label.clear()

    def set_running(self, player_count: int) -> None:
        self.player_label.setText("Analyzing…")
        self.meta_label.setText(f"Comparing {player_count} selected candidates.")
        self.action_label.setText("RUNNING ANALYSIS")
        self.action_label.setProperty("action", "neutral")
        self._refresh(self.action_label)

    def set_recommendations(self, recommendations) -> None:
        recommendations = list(recommendations or ())
        if not recommendations:
            self.reset()
            return

        top = recommendations[0]
        survival = top.survival_probability
        survival_text = f"{survival:.0%}" if survival is not None else "N/A"

        self.player_label.setText(top.player_name)
        self.meta_label.setText(
            f"{top.position}  •  {top.grade}  •  "
            f"{top.primary_strategy}  •  Confidence {top.confidence}%"
        )
        self.score_card.value_label.setText(f"{top.score:.0f}/100")
        self.survival_card.value_label.setText(survival_text)
        self.cost_card.value_label.setText(f"{top.opportunity_cost:+.1f}")
        self.fit_card.value_label.setText(
            f"{top.roster_need} {top.roster_fit_score:+.0f}"
        )

        self.action_label.setText(top.action)
        self.action_label.setProperty("action", self._action_property(top.action))
        self._refresh(self.action_label)

        top_reasons = tuple(top.reasons[:3])
        self.reasons_label.setText(
            "\n".join(f"• {reason}" for reason in top_reasons)
            if top_reasons
            else "This player has the strongest overall recommendation profile."
        )

        alternatives = recommendations[1:4]
        if alternatives:
            alt_text = "   •   ".join(
                f"#{index} {rec.player_name} ({rec.score:.0f})"
                for index, rec in enumerate(alternatives, start=2)
            )
            self.alt_label.setText(f"NEXT:  {alt_text}")
        else:
            self.alt_label.clear()

    @staticmethod
    def _action_property(action: str) -> str:
        if action == "DRAFT NOW":
            return "draft"
        if action == "RISKY TO WAIT":
            return "risk"
        if action in {"CAN PROBABLY WAIT", "SAFE TO WAIT"}:
            return "wait"
        return "neutral"

    @staticmethod
    def _refresh(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


class DraftRoomWorkspace(QWidget):
    """Bottom half of the unified Draft Room."""

    record_requested = Signal(str)
    analyze_requested = Signal(object)
    undo_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("DraftRoomWorkspaceSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(7)

        self.players = DraftRoomPlayerBrowser()
        self.analytics = DraftRoomAnalyticsPanel()

        self.players.record_requested.connect(self.record_requested.emit)
        self.players.analyze_requested.connect(self.analyze_requested.emit)
        self.players.undo_requested.connect(self.undo_requested.emit)

        self.splitter.addWidget(self.players)
        self.splitter.addWidget(self.analytics)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([930, 600])

        layout.addWidget(self.splitter)

    def refresh(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
        recommendations=(),
    ) -> None:
        self.players.refresh(session, approved_players)
        self.analytics.set_recommendations(recommendations)

    def set_analysis_running(self, player_count: int) -> None:
        self.analytics.set_running(player_count)
