from __future__ import annotations

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from asset_manager import DEFAULT_ASSET_MANAGER, short_player_name
from live_draft import LiveDraftSession
from preferences import normalize_name
from projection_loader import load_projections
from coach_message_builder import CoachMessageBuilder
from recommendation_explanation import RecommendationExplanationBuilder
from wait_intelligence import CostOfWaitingBuilder
from team import base_position


POSITION_FILTERS = (
    ("ALL", "ALL"),
    ("QB", "QB"),
    ("RB", "RB"),
    ("WR", "WR"),
    ("TE", "TE"),
    ("FLEX", "FLEX"),
    ("K", "K"),
    ("DEF", "DST"),
)

STARTER_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 1,
    "K": 1,
    "DST": 1,
}

TOTAL_ROSTER_SPOTS = 16

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
    redo_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DraftRoomPlayerBrowser")

        self._session: LiveDraftSession | None = None
        self._approved_players: set[str] = set()
        self._projections = load_projections()
        self._active_position = "ALL"
        self._filter_buttons: dict[str, QPushButton] = {}
        self._known_available_names: set[str] = set()
        self._headshot_icon_cache: dict[str, QIcon] = {}

        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.setInterval(350)
        self._analysis_timer.timeout.connect(self._emit_instant_analysis)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)

        title = QLabel("AVAILABLE PLAYERS")
        title.setObjectName("WorkspaceTitle")
        top.addWidget(title)

        top.addStretch(1)

        self.position_group = QButtonGroup(self)
        self.position_group.setExclusive(True)

        for display_name, position_key in POSITION_FILTERS:
            button = QPushButton()
            button.setObjectName("PositionTab")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumWidth(58 if display_name != "ALL" else 66)
            button.setMinimumHeight(46)
            button.clicked.connect(
                lambda checked=False, key=position_key: self._set_position_filter(key)
            )
            top.addWidget(button)
            self.position_group.addButton(button)
            self._filter_buttons[position_key] = button

        self._filter_buttons["ALL"].setChecked(True)

        layout.addLayout(top)

        self.table = QTableWidget(0, 1)
        self.table.setObjectName("DraftRoomPlayerTable")
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.setWordWrap(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.setIconSize(QPixmap(30, 30).size())
        self.table.viewport().setMouseTracking(True)
        self.table.viewport().installEventFilter(self)

        self._configure_table_columns()
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.itemDoubleClicked.connect(self._double_click)
        layout.addWidget(self.table, 1)

        self.selection_label = QLabel("No player selected")
        self.selection_label.setObjectName("WorkspaceSelection")
        layout.addWidget(self.selection_label)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("WorkspaceSearch")
        self.search.setPlaceholderText("Find player…")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(150)
        self.search.setMaximumWidth(16777215)
        self.search.setFixedHeight(34)
        self.search.textChanged.connect(self.refresh_table)
        actions.addWidget(self.search, 1)

        self.undo_button = QPushButton("UNDO")
        self.undo_button.setObjectName("WorkspaceSecondaryButton")
        self.undo_button.setFixedHeight(34)
        self.undo_button.clicked.connect(self.undo_requested.emit)
        actions.addWidget(self.undo_button)

        self.redo_button = QPushButton("REDO")
        self.redo_button.setObjectName("WorkspaceSecondaryButton")
        self.redo_button.setFixedHeight(34)
        self.redo_button.clicked.connect(self.redo_requested.emit)
        actions.addWidget(self.redo_button)

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
            self._known_available_names.clear()
            self.undo_button.setEnabled(False)
            self.redo_button.setEnabled(False)
            self.refresh_table()
            return
        self.undo_button.setEnabled(bool(session.draft_results))
        self.redo_button.setEnabled(session.can_redo)
        self._refresh_position_tabs()

        new_names = {player.name for player in session.available_players()}
        removed = self._known_available_names - new_names
        added = new_names - self._known_available_names

        if self._known_available_names and len(removed) == 1 and not added:
            self._remove_player_row(next(iter(removed)))
            self._known_available_names = new_names
            self._update_action_state()
            return

        if self._known_available_names and len(added) == 1 and not removed:
            self._insert_player_if_visible(next(iter(added)))
            self._known_available_names = new_names
            self._update_action_state()
            return

        self.refresh_table()

    def _remove_player_row(self, player_name: str) -> None:
        self.table.blockSignals(True)
        try:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) == player_name:
                    self.table.removeRow(row)
                    break
        finally:
            self.table.blockSignals(False)

    def _player_matches_current_view(self, player) -> bool:
        position = base_position(player.position).upper()
        wanted = self._active_position
        if wanted == "FLEX" and position not in {"RB", "WR", "TE"}:
            return False
        if wanted not in {"ALL", "FLEX"} and position != wanted:
            return False
        query = normalize_name(self.search.text())
        return not query or query in normalize_name(player.name)

    def _insert_player_if_visible(self, player_name: str) -> None:
        if self._session is None:
            return
        player = self._session.player_for_name(player_name)
        if player is None or not self._player_matches_current_view(player):
            return

        visible_before = 0
        for candidate in self._session.available_players():
            if candidate.name == player.name:
                break
            if self._player_matches_current_view(candidate):
                visible_before += 1

        self.table.blockSignals(True)
        try:
            self.table.insertRow(visible_before)
            self._populate_player_row(visible_before, player)
        finally:
            self.table.blockSignals(False)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table.viewport():
            event_type = event.type()

            if event_type in {
                QEvent.Type.MouseMove,
                QEvent.Type.Enter,
            }:
                pos = self.table.viewport().mapFromGlobal(QCursor.pos())
                index = self.table.indexAt(pos)
                cursor = (
                    Qt.CursorShape.PointingHandCursor
                    if index.isValid()
                    else Qt.CursorShape.ArrowCursor
                )
                self.table.viewport().setCursor(cursor)

            elif event_type == QEvent.Type.Leave:
                self.table.viewport().setCursor(
                    Qt.CursorShape.ArrowCursor
                )

        return super().eventFilter(watched, event)

    def _set_position_filter(self, position_key: str) -> None:
        self._active_position = position_key
        self._configure_table_columns()
        self.refresh_table()

    def _user_position_counts(self) -> dict[str, int]:
        counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "K": 0, "DST": 0}

        if self._session is None:
            return counts

        for draft_pick in self._session.draft_results:
            if draft_pick.team_number != self._session.user_team_number:
                continue

            position = base_position(draft_pick.player.position).upper()
            if position in counts:
                counts[position] += 1

        return counts

    @staticmethod
    def _flex_filled(counts: dict[str, int]) -> int:
        extras = (
            max(0, counts["RB"] - STARTER_REQUIREMENTS["RB"])
            + max(0, counts["WR"] - STARTER_REQUIREMENTS["WR"])
            + max(0, counts["TE"] - STARTER_REQUIREMENTS["TE"])
        )
        return min(STARTER_REQUIREMENTS["FLEX"], extras)

    def _refresh_position_tabs(self) -> None:
        counts = self._user_position_counts()
        total_drafted = sum(counts.values())
        flex_filled = self._flex_filled(counts)

        for display_name, key in POSITION_FILTERS:
            button = self._filter_buttons.get(key)
            if button is None:
                continue

            if key == "ALL":
                value, maximum = total_drafted, TOTAL_ROSTER_SPOTS
            elif key == "FLEX":
                value, maximum = flex_filled, STARTER_REQUIREMENTS["FLEX"]
            else:
                value = min(counts.get(key, 0), STARTER_REQUIREMENTS[key])
                maximum = STARTER_REQUIREMENTS[key]

            button.setText(f"{display_name}\n{value}/{maximum}")
            button.setProperty(
                "rosterState",
                "complete" if maximum > 0 and value >= maximum else "open",
            )
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _column_schema(self) -> tuple[tuple[str, str], ...]:
        """Return the most useful draft-day columns for the active position tab."""
        position = self._active_position

        if position == "QB":
            return (
                ("RK", "rank"),
                ("PLAYER", "player"),
                ("ADP", "adp"),
                ("BYE", "bye"),
                ("PROJ", "projection"),
                ("PASS YDS", "passing_yards"),
                ("PASS TD", "passing_touchdowns"),
                ("INT", "interceptions"),
                ("RUSH YDS", "rushing_yards"),
                ("RUSH TD", "rushing_touchdowns"),
            )

        if position == "RB":
            return (
                ("RK", "rank"),
                ("PLAYER", "player"),
                ("ADP", "adp"),
                ("BYE", "bye"),
                ("PROJ", "projection"),
                ("RUSH ATT", "rushing_attempts"),
                ("RUSH YDS", "rushing_yards"),
                ("RUSH TD", "rushing_touchdowns"),
                ("REC", "receptions"),
                ("REC YDS", "receiving_yards"),
                ("REC TD", "receiving_touchdowns"),
            )

        if position in {"WR", "TE"}:
            return (
                ("RK", "rank"),
                ("PLAYER", "player"),
                ("ADP", "adp"),
                ("BYE", "bye"),
                ("PROJ", "projection"),
                ("REC", "receptions"),
                ("REC YDS", "receiving_yards"),
                ("REC TD", "receiving_touchdowns"),
                ("RUSH YDS", "rushing_yards"),
                ("RUSH TD", "rushing_touchdowns"),
            )

        if position == "FLEX":
            return (
                ("RK", "rank"),
                ("PLAYER", "player"),
                ("ADP", "adp"),
                ("BYE", "bye"),
                ("PROJ", "projection"),
                ("RUSH YDS", "rushing_yards"),
                ("RUSH TD", "rushing_touchdowns"),
                ("REC", "receptions"),
                ("REC YDS", "receiving_yards"),
                ("REC TD", "receiving_touchdowns"),
            )

        if position == "K":
            return (
                ("RK", "rank"),
                ("PLAYER", "player"),
                ("BYE", "bye"),
                ("PROJ", "projection"),
                ("FG", "field_goals_made"),
                ("FGA", "field_goals_attempted"),
                ("XP", "extra_points_made"),
            )

        if position == "DST":
            return (
                ("RK", "rank"),
                ("PLAYER", "player"),
                ("BYE", "bye"),
                ("PROJ", "projection"),
                ("SACK", "sacks"),
                ("INT", "interceptions"),
                ("FR", "fumble_recoveries"),
                ("TD", "touchdowns"),
                ("PA", "points_allowed"),
            )

        # ALL remains intentionally compact for fast browsing.
        return (
            ("RK", "rank"),
            ("PLAYER", "player"),
            ("ADP", "adp"),
            ("BYE", "bye"),
            ("PROJ", "projection"),
            ("TIER", "tier"),
            ("POS", "position"),
        )

    def _configure_table_columns(self) -> None:
        schema = self._column_schema()
        self.table.setColumnCount(len(schema))
        self.table.setHorizontalHeaderLabels(tuple(title for title, _key in schema))

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)

        # ResizeToContents is surprisingly expensive on a frequently rebuilt
        # QTableWidget because Qt keeps measuring cell contents. Keep PLAYER fluid
        # and use predictable widths for the numeric/stat columns instead.
        widths = {
            "rank": 56,
            "adp": 54,
            "bye": 46,
            "projection": 62,
            "tier": 46,
            "position": 82,
            "passing_yards": 72,
            "passing_touchdowns": 62,
            "interceptions": 48,
            "rushing_attempts": 68,
            "rushing_yards": 72,
            "rushing_touchdowns": 62,
            "receptions": 52,
            "receiving_yards": 72,
            "receiving_touchdowns": 62,
            "field_goals_made": 52,
            "field_goals_attempted": 52,
            "extra_points_made": 52,
            "sacks": 52,
            "fumble_recoveries": 48,
            "touchdowns": 48,
            "points_allowed": 48,
        }

        for column, (_title, key) in enumerate(schema):
            if key == "player":
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(column, widths.get(key, 58))

    @staticmethod
    def _format_stat(value: float | int | None) -> str:
        if value is None:
            return "—"

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return "—"

        if abs(numeric) < 0.0001:
            return "0"

        if numeric.is_integer():
            return str(int(numeric))

        return f"{numeric:.1f}"

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

    def _headshot_icon(self, player_name: str) -> QIcon | None:
        cached = self._headshot_icon_cache.get(player_name)
        if cached is not None:
            return cached
        path = DEFAULT_ASSET_MANAGER.headshot(player_name)
        if path is None:
            return None
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        scaled = pixmap.scaled(
            30, 30,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon = QIcon(scaled)
        self._headshot_icon_cache[player_name] = icon
        return icon

    @staticmethod
    def _tier_palette(tier: int | None) -> tuple[str, str]:
        """Subtle tier colors: useful at a glance without turning the table into a rainbow."""
        palettes = {
            1: ("#bbf7d0", "#123022"),
            2: ("#bae6fd", "#12324a"),
            3: ("#fde68a", "#3f3510"),
            4: ("#fed7aa", "#422d15"),
            5: ("#fecdd3", "#40202a"),
        }
        if isinstance(tier, int) and tier > 0:
            return palettes.get(tier, ("#cbd5e1", "#263244"))
        return "#94a3b8", "#1b2534"

    def _populate_player_row(self, row: int, player) -> None:
        position = base_position(player.position).upper()
        projection = self._projections.get(normalize_name(player.name))
        stats = projection.stats if projection is not None else {}
        projected_points = projection.fantasy_points if projection is not None else None
        schema = self._column_schema()
        self.table.setRowHeight(row, 40)

        for column, (_title, key) in enumerate(schema):
            if key == "player":
                my_guy = normalize_name(player.name) in self._approved_players
                text = (
                    f"{short_player_name(player.name)}{'   ★' if my_guy else ''}\n"
                    f"{player.position}  •  {player.team}"
                )
                item = QTableWidgetItem(text)
                item.setForeground(QColor("#fde047" if my_guy else "#f8fafc"))
                icon = self._headshot_icon(player.name)
                if icon is not None:
                    item.setIcon(icon)
            elif key == "rank":
                item = QTableWidgetItem(str(getattr(player, "rank", "") or "—"))
            elif key == "adp":
                adp = getattr(player, "adp", None)
                item = QTableWidgetItem(f"{float(adp):.1f}" if isinstance(adp, (int, float)) else "—")
            elif key == "bye":
                item = QTableWidgetItem(str(getattr(player, "bye", "") or "—"))
            elif key == "projection":
                item = QTableWidgetItem(f"{projected_points:.1f}" if isinstance(projected_points, (int, float)) else "—")
            elif key == "tier":
                tier = getattr(player, "tier", None)
                item = QTableWidgetItem(str(tier or "—"))
                tier_fg, tier_bg = self._tier_palette(tier)
                item.setForeground(QColor(tier_fg))
                item.setBackground(QColor(tier_bg))
                if isinstance(tier, int) and tier > 0:
                    item.setToolTip(
                        f"Tier {tier} — lower tier numbers indicate stronger projection groups."
                    )
            elif key == "position":
                item = QTableWidgetItem(f"{player.position}  {player.team}")
                item.setForeground(QColor(POSITION_COLORS.get(position, "#e2e8f0")))
            else:
                item = QTableWidgetItem(self._format_stat(stats.get(key)))
                if key.endswith("touchdowns") or key == "touchdowns":
                    item.setForeground(QColor("#facc15"))

            item.setData(Qt.ItemDataRole.UserRole, player.name)
            if key != "player":
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, column, item)

    def refresh_table(self) -> None:
        previously_selected = set(self.selected_player_names())
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        try:
            if self._session is None:
                self._known_available_names.clear()
                return

            available_players = self._session.available_players()
            visible_players = [
                player
                for player in available_players
                if self._player_matches_current_view(player)
            ]

            # Allocate the final table shape once. Repeated insertRow() calls cause
            # Qt to shift its internal model/layout on every player.
            self.table.setRowCount(len(visible_players))

            for row, player in enumerate(visible_players):
                self._populate_player_row(row, player)
                if player.name in previously_selected:
                    self.table.selectRow(row)

            self._known_available_names = {
                player.name for player in available_players
            }
        finally:
            self.table.blockSignals(False)
            self.table.setUpdatesEnabled(True)

        self._update_action_state()

    def _selection_changed(self) -> None:
        self._update_action_state()

        if (
            self._session is None
            or not self._session.is_user_turn
            or self._session.is_complete
        ):
            self._analysis_timer.stop()
            return

        if not self.selected_player_names():
            self._analysis_timer.stop()
            return

        # Debounce rapid Cmd-click selection changes into one analysis.
        self._analysis_timer.start()

    def _emit_instant_analysis(self) -> None:
        names = self.selected_player_names()
        if (
            names
            and self._session is not None
            and self._session.is_user_turn
            and not self._session.is_complete
        ):
            self.analyze_requested.emit(names)

    def _update_action_state(self) -> None:
        names = self.selected_player_names()
        count = len(names)
        can_record = bool(self._session and not self._session.is_complete and count == 1)

        self.record_button.setEnabled(can_record)

        if count == 0:
            self.selection_label.setText("No player selected")
            self.record_button.setText("RECORD PICK")
        elif count == 1:
            self.record_button.setText("RECORD PICK")
            if self._session is not None and self._session.is_user_turn:
                self.selection_label.setText(f"{names[0]}  •  AI updates automatically")
            else:
                self.selection_label.setText(names[0])
        else:
            self.selection_label.setText(
                f"{count} candidates selected  •  AI comparing automatically"
            )

    def _record(self) -> None:
        names = self.selected_player_names()
        if len(names) == 1:
            self.record_requested.emit(names[0])

    def _double_click(self, item: QTableWidgetItem) -> None:
        value = item.data(Qt.ItemDataRole.UserRole)
        if value:
            self.record_requested.emit(str(value))


class DraftRoomRosterPanel(QFrame):
    """Live starter-slot roster view for the user's team."""

    STARTER_SLOTS = (
        ("QB", ("QB",)),
        ("RB", ("RB",)),
        ("RB", ("RB",)),
        ("WR", ("WR",)),
        ("WR", ("WR",)),
        ("TE", ("TE",)),
        ("FLEX", ("RB", "WR", "TE")),
        ("D/ST", ("DST",)),
        ("K", ("K",)),
    )
    BENCH_SLOTS = 7

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DraftRoomRosterPanel")
        self._slot_rows: list[tuple[QLabel, QLabel, QLabel]] = []
        self._projections = load_projections()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("MY ROSTER")
        title.setObjectName("WorkspaceTitle")
        layout.addWidget(title)

        self.summary_label = QLabel("0 / 16 roster spots filled")
        self.summary_label.setObjectName("WorkspaceSubtle")
        layout.addWidget(self.summary_label)

        self.rows_host = QWidget()
        rows_layout = QVBoxLayout(self.rows_host)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(3)

        for slot_name, _eligible in self.STARTER_SLOTS:
            rows_layout.addWidget(self._make_slot_row(slot_name, starter=True))

        bench_header = QLabel("BENCH")
        bench_header.setObjectName("RosterBenchHeader")
        rows_layout.addWidget(bench_header)

        for _ in range(self.BENCH_SLOTS):
            rows_layout.addWidget(self._make_slot_row("BN", starter=False))

        rows_layout.addStretch(1)
        layout.addWidget(self.rows_host, 1)

    def _make_slot_row(self, slot_name: str, *, starter: bool) -> QFrame:
        frame = QFrame()
        frame.setObjectName("RosterSlotRow")
        frame.setProperty("starter", "true" if starter else "false")

        row = QHBoxLayout(frame)
        row.setContentsMargins(7, 4, 7, 4)
        row.setSpacing(6)

        slot_label = QLabel(slot_name)
        slot_label.setObjectName("RosterSlotLabel")
        slot_label.setFixedWidth(34)
        row.addWidget(slot_label)

        player_label = QLabel("—")
        player_label.setObjectName("RosterPlayer")
        player_label.setWordWrap(False)
        row.addWidget(player_label, 1)

        team_label = QLabel("")
        team_label.setObjectName("RosterTeam")
        team_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        team_label.setFixedWidth(36)
        row.addWidget(team_label)

        self._slot_rows.append((slot_label, player_label, team_label))
        return frame

    def _projected_points(self, player) -> float:
        projection = self._projections.get(normalize_name(player.name))
        if projection is None:
            return float("-inf")
        return float(projection.fantasy_points)

    def _best_player_index(
        self,
        players: list,
        eligible_positions: tuple[str, ...] | set[str],
    ) -> int | None:
        eligible = [
            (index, player)
            for index, player in enumerate(players)
            if base_position(player.position).upper() in eligible_positions
        ]
        if not eligible:
            return None

        return max(
            eligible,
            key=lambda pair: (
                self._projected_points(pair[1]),
                -int(getattr(pair[1], "rank", 9999) or 9999),
            ),
        )[0]

    def refresh(self, session: LiveDraftSession | None) -> None:
        # Clear every slot first.
        for _slot_label, player_label, team_label in self._slot_rows:
            player_label.setText("—")
            player_label.setStyleSheet("")
            team_label.clear()

        if session is None:
            self.summary_label.setText("0 / 16 roster spots filled")
            return

        user_players = [
            draft_pick.player
            for draft_pick in session.draft_results
            if draft_pick.team_number == session.user_team_number
        ]
        self.summary_label.setText(f"{len(user_players)} / 16 roster spots filled")

        remaining = list(user_players)
        assignments: list[object | None] = []

        # Starter slots always use the strongest projected eligible players.
        # That keeps the visible lineup optimized instead of preserving draft order.
        strict_slots = self.STARTER_SLOTS[:6]
        for _slot_name, eligible_positions in strict_slots:
            chosen_index = self._best_player_index(
                remaining,
                eligible_positions,
            )
            if chosen_index is None:
                assignments.append(None)
            else:
                assignments.append(remaining.pop(chosen_index))

        # FLEX is the highest-projected remaining RB/WR/TE after the base
        # QB/RB/RB/WR/WR/TE starters have been filled.
        flex_index = self._best_player_index(
            remaining,
            {"RB", "WR", "TE"},
        )
        if flex_index is None:
            assignments.append(None)
        else:
            assignments.append(remaining.pop(flex_index))

        # D/ST then K use their dedicated starter slots.
        for wanted in ("DST", "K"):
            chosen_index = self._best_player_index(
                remaining,
                {wanted},
            )
            if chosen_index is None:
                assignments.append(None)
            else:
                assignments.append(remaining.pop(chosen_index))

        # Bench is an at-a-glance depth chart: highest projected first.
        remaining.sort(
            key=lambda player: (
                self._projected_points(player),
                -int(getattr(player, "rank", 9999) or 9999),
            ),
            reverse=True,
        )
        assignments.extend(remaining[: self.BENCH_SLOTS])
        while len(assignments) < len(self._slot_rows):
            assignments.append(None)

        for row_index, player in enumerate(assignments[: len(self._slot_rows)]):
            _slot_label, player_label, team_label = self._slot_rows[row_index]
            if player is None:
                continue

            player_label.setText(player.name)
            position = base_position(player.position).upper()
            color = POSITION_COLORS.get(position, "#e2e8f0")
            player_label.setStyleSheet(f"color: {color}; font-weight: 850;")
            team_label.setText(player.team)


class DraftRoomAnalyticsPanel(QFrame):
    """Ultra-compact live-draft recommendation panel.

    Default view answers only:
      1) Who should I draft?
      2) How strongly?
      3) Why?
      4) What's Plan B?

    Everything else is hidden behind one More Analysis disclosure.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DraftRoomAnalyticsPanel")
        self._session: LiveDraftSession | None = None
        self._forecast = None
        self._recommendation_mode = "auto"

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QPropertyAnimation(
            self._opacity_effect,
            b"opacity",
            self,
        )
        self._fade_animation.setDuration(150)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._build_ui()
        self.reset()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(9)

        # -------------------------------------------------------------
        # HERO
        # -------------------------------------------------------------
        hero = QFrame()
        hero.setObjectName("GlanceHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(13, 11, 13, 11)
        hero_layout.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.mode_label = QLabel("GRIDIRON'S PICK")
        self.mode_label.setObjectName("GlanceMode")
        top.addWidget(self.mode_label)

        top.addStretch(1)

        self.confidence_label = QLabel("—")
        self.confidence_label.setObjectName("GlanceConfidence")
        top.addWidget(self.confidence_label)

        hero_layout.addLayout(top)

        self.player_label = QLabel("Waiting for your pick")
        self.player_label.setObjectName("GlancePlayer")
        self.player_label.setWordWrap(False)
        hero_layout.addWidget(self.player_label)

        self.meta_label = QLabel("Gridiron will choose automatically.")
        self.meta_label.setObjectName("GlanceMeta")
        hero_layout.addWidget(self.meta_label)

        score_row = QHBoxLayout()
        score_row.setSpacing(8)

        self.score_label = QLabel("—")
        self.score_label.setObjectName("GlanceScore")
        score_row.addWidget(self.score_label)

        self.grade_label = QLabel("READY")
        self.grade_label.setObjectName("GlanceGrade")
        score_row.addWidget(self.grade_label)

        score_row.addStretch(1)

        hero_layout.addLayout(score_row)

        self.action_label = QLabel("WAITING")
        self.action_label.setObjectName("AnalyticsAction")
        self.action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.action_label)

        layout.addWidget(hero)

        # -------------------------------------------------------------
        # WHY — no paragraph, just short glanceable reasons.
        # -------------------------------------------------------------
        why_title = QLabel("WHY")
        why_title.setObjectName("AnalyticsSectionTitle")
        layout.addWidget(why_title)

        self.reasons_label = QLabel("Waiting for analysis.")
        self.reasons_label.setObjectName("GlanceReasons")
        self.reasons_label.setWordWrap(True)
        layout.addWidget(self.reasons_label)

        # -------------------------------------------------------------
        # PLAN B — open by default because this is draft-day useful.
        # -------------------------------------------------------------
        plan_title = QLabel("PLAN B")
        plan_title.setObjectName("AnalyticsSectionTitle")
        layout.addWidget(plan_title)

        self.alt_label = QLabel("—")
        self.alt_label.setObjectName("GlanceAlternatives")
        self.alt_label.setWordWrap(True)
        layout.addWidget(self.alt_label)

        # -------------------------------------------------------------
        # ONE disclosure for all nerd-mode information.
        # -------------------------------------------------------------
        self.more_button = QToolButton()
        self.more_button.setObjectName("GlanceMoreButton")
        self.more_button.setText("More analysis")
        self.more_button.setCheckable(True)
        self.more_button.setChecked(False)
        self.more_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.more_button.setArrowType(Qt.ArrowType.RightArrow)
        self.more_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.more_button)

        self.more_content = QFrame()
        self.more_content.setObjectName("GlanceMoreContent")
        more_layout = QVBoxLayout(self.more_content)
        more_layout.setContentsMargins(10, 9, 10, 9)
        more_layout.setSpacing(10)

        # Compact core metrics live only inside More Analysis.
        metrics_title = QLabel("CORE METRICS")
        metrics_title.setObjectName("GlanceAdvancedTitle")
        more_layout.addWidget(metrics_title)

        metrics = QGridLayout()
        metrics.setSpacing(6)
        self.tier_metric = self._metric("TIER")
        self.survival_metric = self._metric("SURVIVES")
        self.wait_metric = self._metric("WAIT VALUE")
        metrics.addWidget(self.tier_metric, 0, 0)
        metrics.addWidget(self.survival_metric, 0, 1)
        metrics.addWidget(self.wait_metric, 0, 2)
        more_layout.addLayout(metrics)

        timeline_title = QLabel("WHAT I'M EXPECTING NEXT")
        timeline_title.setObjectName("GlanceAdvancedTitle")
        more_layout.addWidget(timeline_title)

        self.timeline_meta = QLabel("—")
        self.timeline_meta.setObjectName("DraftTimelineMeta")
        self.timeline_meta.setWordWrap(True)
        more_layout.addWidget(self.timeline_meta)

        self.timeline_grid = QGridLayout()
        self.timeline_grid.setContentsMargins(0, 0, 0, 0)
        self.timeline_grid.setHorizontalSpacing(5)
        self.timeline_grid.setVerticalSpacing(5)
        more_layout.addLayout(self.timeline_grid)

        self.timeline_summary = QLabel("Expected before next pick: —")
        self.timeline_summary.setObjectName("DraftTimelineSummary")
        self.timeline_summary.setWordWrap(True)
        more_layout.addWidget(self.timeline_summary)

        wait_title = QLabel("WHAT HAPPENS IF YOU WAIT?")
        wait_title.setObjectName("GlanceAdvancedTitle")
        more_layout.addWidget(wait_title)

        self.wait_headline_label = QLabel("—")
        self.wait_headline_label.setObjectName("WaitIntelHeadline")
        more_layout.addWidget(self.wait_headline_label)

        self.wait_detail_label = QLabel("—")
        self.wait_detail_label.setObjectName("CoachAdvancedText")
        self.wait_detail_label.setWordWrap(True)
        more_layout.addWidget(self.wait_detail_label)

        score_title = QLabel("SCORE BREAKDOWN")
        score_title.setObjectName("GlanceAdvancedTitle")
        more_layout.addWidget(score_title)

        self.score_breakdown_label = QLabel("—")
        self.score_breakdown_label.setObjectName("CoachAdvancedText")
        self.score_breakdown_label.setWordWrap(True)
        more_layout.addWidget(self.score_breakdown_label)

        sim_title = QLabel("SIMULATOR")
        sim_title.setObjectName("GlanceAdvancedTitle")
        more_layout.addWidget(sim_title)

        self.simulator_label = QLabel("—")
        self.simulator_label.setObjectName("CoachAdvancedText")
        self.simulator_label.setWordWrap(True)
        more_layout.addWidget(self.simulator_label)

        self.more_content.setVisible(False)
        self.more_button.toggled.connect(self._toggle_more)
        layout.addWidget(self.more_content)

        layout.addStretch(1)

    @staticmethod
    def _metric(title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("CoachSignalCard")
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(6, 5, 6, 5)
        card_layout.setSpacing(1)

        title_label = QLabel(title)
        title_label.setObjectName("CoachSignalTitle")

        value_label = QLabel("—")
        value_label.setObjectName("CoachSignalValue")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        frame.value_label = value_label
        return frame

    def _toggle_more(self, checked: bool) -> None:
        self.more_content.setVisible(checked)
        self.more_button.setArrowType(
            Qt.ArrowType.DownArrow
            if checked
            else Qt.ArrowType.RightArrow
        )

    def _animate_refresh(self) -> None:
        self._fade_animation.stop()
        self._opacity_effect.setOpacity(0.78)
        self._fade_animation.setStartValue(0.78)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.start()

    def _clear_timeline(self) -> None:
        while self.timeline_grid.count():
            item = self.timeline_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _timeline_position_color(position: str | None) -> str:
        return {
            "QB": "#a855f7",
            "RB": "#34d399",
            "WR": "#38bdf8",
            "TE": "#fb923c",
        }.get(position or "", "#64748b")

    def _populate_timeline(self) -> None:
        self._clear_timeline()

        if self._forecast is None:
            self.timeline_meta.setText("No next-pick forecast available.")
            self.timeline_summary.setText("Expected before next pick: —")
            return

        self.timeline_meta.setText(
            f"Pick {self._forecast.current_pick} → "
            f"{self._forecast.next_user_pick}  •  "
            f"{self._forecast.picks_between} picks between"
        )

        for index, pick_forecast in enumerate(
            tuple(getattr(self._forecast, "pick_forecasts", ()))
        ):
            row = index // 5
            column = index % 5
            position = pick_forecast.most_likely_position or "—"
            probability = float(pick_forecast.probability or 0.0)

            chip = QFrame()
            chip.setObjectName("DraftTimelineChip")
            chip_layout = QVBoxLayout(chip)
            chip_layout.setContentsMargins(5, 4, 5, 4)
            chip_layout.setSpacing(1)

            pick_label = QLabel(str(pick_forecast.overall_pick))
            pick_label.setObjectName("DraftTimelinePick")
            pick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            pos_label = QLabel(position)
            pos_label.setObjectName("DraftTimelinePosition")
            pos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pos_label.setStyleSheet(
                f"color: {self._timeline_position_color(position)};"
            )

            prob_label = QLabel(f"{probability:.0%}")
            prob_label.setObjectName("DraftTimelineProbability")
            prob_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            chip_layout.addWidget(pick_label)
            chip_layout.addWidget(pos_label)
            chip_layout.addWidget(prob_label)

            distribution = " • ".join(
                f"{pos} {prob:.0%}"
                for pos, prob in pick_forecast.position_probabilities
            )
            chip.setToolTip(
                f"Pick {pick_forecast.overall_pick}\n"
                f"Team {pick_forecast.team_number}\n"
                f"Most likely: {position} ({probability:.0%})\n"
                f"{distribution}"
            )

            self.timeline_grid.addWidget(chip, row, column)

        by_position = {
            item.position: item
            for item in self._forecast.position_forecasts
        }
        parts = []
        for position in ("QB", "RB", "WR", "TE"):
            forecast = by_position.get(position)
            if forecast is not None:
                parts.append(f"{position} {forecast.expected_picks:.1f}")

        self.timeline_summary.setText(
            "Expected before next pick:  " + "  •  ".join(parts)
            if parts
            else "Expected before next pick: —"
        )

    def reset(self) -> None:
        self.mode_label.setText("GRIDIRON'S PICK")
        self.confidence_label.setText("—")
        self.player_label.setText("Waiting for your pick")
        self.meta_label.setText("Gridiron will choose automatically.")
        self.score_label.setText("—")
        self.grade_label.setText("READY")

        self.action_label.setText("WAITING")
        self.action_label.setProperty("action", "neutral")
        self._refresh(self.action_label)

        self.reasons_label.setText("Waiting for analysis.")
        self.alt_label.setText("—")

        self.tier_metric.value_label.setText("—")
        self.survival_metric.value_label.setText("—")
        self.wait_metric.value_label.setText("—")

        self._clear_timeline()
        self.timeline_meta.setText("No next-pick forecast available.")
        self.timeline_summary.setText("Expected before next pick: —")
        self.wait_headline_label.setText("—")
        self.wait_detail_label.setText("—")
        self.score_breakdown_label.setText("—")
        self.simulator_label.setText("—")

        self.more_button.setChecked(False)

    def set_context(
        self,
        session: LiveDraftSession | None,
        forecast=None,
        recommendation_mode: str = "auto",
    ) -> None:
        self._session = session
        self._forecast = forecast
        self._recommendation_mode = recommendation_mode
        self._populate_timeline()

    def set_running(self, player_count: int) -> None:
        self._animate_refresh()
        self.mode_label.setText(
            "GRIDIRON'S PICK"
            if self._recommendation_mode == "auto"
            else "WHAT-IF"
        )
        self.player_label.setText("Analyzing…")
        self.meta_label.setText(
            f"Comparing {player_count} "
            f"{'candidate' if player_count == 1 else 'candidates'}."
        )
        self.score_label.setText("—")
        self.grade_label.setText("WORKING")
        self.action_label.setText("ANALYZING")
        self.action_label.setProperty("action", "neutral")
        self._refresh(self.action_label)

    def set_recommendations(self, recommendations) -> None:
        recommendations = list(recommendations or ())
        if not recommendations:
            self.reset()
            return

        self._animate_refresh()
        self._populate_timeline()

        top = recommendations[0]
        explanation = RecommendationExplanationBuilder.build(
            top,
            recommendations[1:],
        )

        self.mode_label.setText(
            "GRIDIRON'S PICK"
            if self._recommendation_mode == "auto"
            else "WHAT-IF"
        )
        self.confidence_label.setText(f"{top.confidence}% CONFIDENCE")
        self.player_label.setText(top.player_name)

        strategy = str(getattr(top, "primary_strategy", "") or "").strip()
        meta = [str(top.position).upper()]
        team = str(getattr(top, "team", "") or "").strip()
        if team:
            meta.append(team)
        if strategy:
            meta.append(strategy)
        self.meta_label.setText("  •  ".join(meta))

        self.score_label.setText(explanation.score_text)
        self.grade_label.setText(explanation.headline)

        self.action_label.setText(explanation.action)
        self.action_label.setProperty(
            "action",
            self._action_property(explanation.action),
        )
        self._refresh(self.action_label)

        # Keep only three compact reasons by default and shorten common verbose
        # engine explanations into draft-at-a-glance fragments.
        reasons = [
            self._compact_reason(reason)
            for reason in explanation.reasons[:3]
        ]
        self.reasons_label.setText(
            "\n".join(f"✓  {reason}" for reason in reasons)
            if reasons
            else "No single factor dominates this pick."
        )

        self.alt_label.setText(
            "\n".join(self._compact_alternative(line) for line in explanation.alternatives[:3])
            if explanation.alternatives
            else "No close alternative."
        )

        self.tier_metric.value_label.setText(explanation.tier_text)
        self.survival_metric.value_label.setText(explanation.survival_text)
        self.wait_metric.value_label.setText(explanation.pass_cost_text)

        wait_view = CostOfWaitingBuilder.build(
            top,
            current_pick=(
                self._session.current_pick
                if self._session is not None
                else None
            ),
            next_pick=(
                self._session.next_user_pick
                if self._session is not None
                else None
            ),
        )
        self.wait_headline_label.setText(wait_view.headline)
        self.wait_headline_label.setProperty("risk", wait_view.risk_level)
        self._refresh(self.wait_headline_label)
        self.wait_detail_label.setText(
            f"{wait_view.pick_window}\n"
            f"{wait_view.point_swing_detail}\n"
            f"{wait_view.take_path_text}\n"
            f"{wait_view.pass_path_text}"
        )

        component_lines = []
        for name, earned, maximum in top.score_breakdown.component_items():
            component_lines.append(
                f"{name:<18} {earned:>4.1f} / {maximum:.0f}"
            )
        self.score_breakdown_label.setText("\n".join(component_lines))

        if self._forecast is None:
            self.simulator_label.setText(
                "Final pick: no next-pick forecast required."
            )
        else:
            position_forecast = self._forecast.position(top.position)
            run_text = (
                f"{position_forecast.expected_picks:.1f} expected {top.position} picks • "
                f"{position_forecast.run_probability:.0%} run probability"
                if position_forecast is not None
                else "No position-run forecast."
            )
            self.simulator_label.setText(
                f"{self._forecast.simulations} simulations • "
                f"{self._forecast.picks_between} picks until your next turn\n"
                f"{run_text}"
            )

    @staticmethod
    def _compact_reason(reason: str) -> str:
        text = str(reason).strip().rstrip(".")
        replacements = (
            ("Last available player in ", "Last "),
            ("Only ", ""),
            (" chance he survives to your next pick", " survives to next pick"),
            ("Run pressure: ", ""),
            (" expected ", " "),
            (" picks before your next turn", "s projected before next pick"),
            ("Taking him now projects ", "+"),
            (" more roster pts than the pass path", " pts vs waiting"),
            ("Simulator expects ", ""),
        )
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    @staticmethod
    def _compact_alternative(line: str) -> str:
        text = str(line).strip()
        # Builder emits "#2  Name  •  82/100 • 40% survives".
        return text.replace("  •  ", "   ")

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
    """Bottom workspace: Available Players | My Roster | Gridiron AI."""

    record_requested = Signal(str)
    analyze_requested = Signal(object)
    undo_requested = Signal()
    redo_requested = Signal()

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
        self.roster = DraftRoomRosterPanel()
        self.analytics = DraftRoomAnalyticsPanel()

        self.players.record_requested.connect(self.record_requested.emit)
        self.players.analyze_requested.connect(self.analyze_requested.emit)
        self.players.undo_requested.connect(self.undo_requested.emit)
        self.players.redo_requested.connect(self.redo_requested.emit)

        self.splitter.addWidget(self.players)
        self.splitter.addWidget(self.roster)
        self.splitter.addWidget(self.analytics)

        # The AI panel is the product centerpiece. Keep Available Players
        # useful without letting its toolbar dictate the entire workspace width.
        self.splitter.setStretchFactor(0, 41)
        self.splitter.setStretchFactor(1, 18)
        self.splitter.setStretchFactor(2, 41)
        self.splitter.setSizes([620, 270, 630])

        self.players.setMinimumWidth(550)
        self.roster.setMinimumWidth(225)
        self.analytics.setMinimumWidth(470)

        layout.addWidget(self.splitter)

    def refresh(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
        recommendations=(),
        forecast=None,
        recommendation_mode: str = "auto",
    ) -> None:
        self.players.refresh(session, approved_players)
        self.roster.refresh(session)
        self.analytics.set_context(session, forecast, recommendation_mode)
        self.analytics.set_recommendations(recommendations)

    def set_analysis_running(self, player_count: int) -> None:
        self.analytics.set_running(player_count)
