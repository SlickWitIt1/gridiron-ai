from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QSplitter, QVBoxLayout, QWidget

from live_draft import LiveDraftSession
from ui.draft_board_widget import DraftBoardWidget
from ui.draft_room_workspace import DraftRoomWorkspace


DRAFT_BOARD_STYLESHEET = r"""
QDialog {
    background-color: #0b1020;
    color: #f8fafc;
}

QLabel {
    background: transparent;
}

QFrame#DraftRoomHeaderCard {
    background-color: #101725;
    border: 1px solid #243248;
    border-radius: 14px;
}

QLabel#DraftRoomTitle {
    color: #f8fafc;
    font-size: 19px;
    font-weight: 950;
    letter-spacing: 1px;
}

QLabel#DraftRoomSummary {
    color: #8ea0b8;
    font-size: 12px;
}

QLabel#DraftRoomMetaTitle {
    color: #64748b;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1px;
}

QLabel#DraftRoomProgressPercent {
    color: #cbd5e1;
    font-size: 10px;
    font-weight: 950;
}

QProgressBar#DraftRoomProgress {
    background-color: #202b3d;
    border: 0;
    border-radius: 5px;
}

QProgressBar#DraftRoomProgress::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}

QLabel#DraftRoomOnClock {
    background-color: #182235;
    border: 1px solid #334155;
    border-radius: 9px;
    color: #cbd5e1;
    font-size: 11px;
    font-weight: 900;
    padding: 8px 10px;
}

QLabel#DraftRoomOnClock[userTurn="true"] {
    background-color: #123022;
    border-color: #22c55e;
    color: #86efac;
}

QScrollArea#DraftBoardScroll,
QWidget#DraftBoardCanvas {
    background-color: #0b1020;
    border: 0;
}

QLabel#DraftRoundHeader,
QLabel#DraftRoundLabel {
    background-color: #111827;
    border: 1px solid #243248;
    border-radius: 8px;
    color: #64748b;
    font-size: 10px;
    font-weight: 900;
}

QFrame#DraftTeamHeader {
    background-color: #111827;
    border: 1px solid #243248;
    border-radius: 10px;
}

QFrame#DraftTeamHeader[userTeam="true"] {
    background-color: #142b4d;
    border: 1px solid #3b82f6;
}

QLabel#DraftTeamName {
    color: #e5edf8;
    font-size: 11px;
    font-weight: 950;
}

QFrame#DraftTeamHeader[userTeam="true"] QLabel#DraftTeamName {
    color: #93c5fd;
}

QFrame#DraftCardContent {
    background-color: transparent;
    border: 0;
}

QLabel#DraftCardTeamLogo,
QLabel#DraftCardHeadshot {
    background-color: transparent;
    border: 0;
}

QFrame#DraftPickCard {
    background-color: #121a28;
    border: 1px solid #253248;
    border-radius: 10px;
}

QFrame#DraftPickCard[position="rb"] {
    background-color: #0f5a43;
    border-color: #197a5b;
}

QFrame#DraftPickCard[position="wr"] {
    background-color: #0f536b;
    border-color: #197694;
}

QFrame#DraftPickCard[position="qb"] {
    background-color: #55295f;
    border-color: #7f448c;
}

QFrame#DraftPickCard[position="te"] {
    background-color: #6a4319;
    border-color: #946124;
}

QFrame#DraftPickCard[position="dst"] {
    background-color: #374151;
    border-color: #64748b;
}

QFrame#DraftPickCard[position="k"] {
    background-color: #5b5218;
    border-color: #8a7d24;
}

QFrame#DraftPickCard[userTeam="true"] {
    border: 1px solid #3b82f6;
}

QFrame#DraftPickCard[hovered="true"] {
    border: 2px solid #7dd3fc;
}

QFrame#DraftPickCard[currentPick="true"] {
    background-color: #18233a;
    border: 2px solid #facc15;
}

QFrame#DraftPickCard[currentPick="true"][pulse="true"] {
    border: 3px solid #fde047;
}

QLabel#DraftCardPick {
    color: #a7b6ca;
    font-size: 10px;
    font-weight: 900;
}

QLabel#DraftCardPlayer {
    color: #ffffff;
    font-size: 12px;
    font-weight: 950;
}

QLabel#DraftCardPosition {
    color: #f1f5f9;
    font-size: 10px;
    font-weight: 950;
}

QLabel#DraftCardTeam {
    color: #d4deeb;
    font-size: 9px;
    font-weight: 750;
}

QLabel#DraftCardClockBadge {
    background-color: #3a3005;
    border: 1px solid #facc15;
    border-radius: 7px;
    color: #fde047;
    font-size: 8px;
    font-weight: 950;
    padding: 2px 8px;
}

QFrame#DraftRoomFooter {
    background-color: #101725;
    border: 1px solid #243248;
    border-radius: 10px;
}

QLabel#DraftRoomLegendText,
QLabel#DraftRoomHoverIntel {
    color: #8ea0b8;
    font-size: 10px;
    font-weight: 700;
}

QLabel#DraftRoomHoverIntel[active="true"] {
    color: #e2e8f0;
    font-weight: 850;
}

/* --- Unified workspace --- */

QSplitter#DraftRoomMainSplitter::handle,
QSplitter#DraftRoomWorkspaceSplitter::handle {
    background-color: #182235;
}

QSplitter#DraftRoomMainSplitter::handle:hover,
QSplitter#DraftRoomWorkspaceSplitter::handle:hover {
    background-color: #334155;
}

QFrame#DraftRoomPlayerBrowser,
QFrame#DraftRoomRosterPanel,
QFrame#DraftRoomAnalyticsPanel {
    background-color: #101725;
    border: 1px solid #243248;
    border-radius: 11px;
}

QLabel#WorkspaceTitle,
QLabel#AnalyticsEyebrow {
    color: #f8fafc;
    font-size: 11px;
    font-weight: 950;
    letter-spacing: .8px;
}


QPushButton#PositionTab {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    color: #94a3b8;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 900;
}

QPushButton#PositionTab:hover {
    background-color: #172033;
    color: #e2e8f0;
}

QPushButton#PositionTab:checked {
    background-color: #0f766e;
    border-color: #14b8a6;
    color: #ecfeff;
}

QPushButton#PositionTab[rosterState="complete"]:!checked {
    color: #4ade80;
}

QLabel#WorkspaceSubtle,
QLabel#AnalyticsMeta {
    color: #8091aa;
    font-size: 9px;
    font-weight: 700;
}

QLineEdit#WorkspaceSearch,
QComboBox#WorkspaceFilter {
    background-color: #182235;
    border: 1px solid #334155;
    border-radius: 7px;
    color: #e2e8f0;
    padding: 5px 8px;
    min-height: 23px;
}

QLineEdit#WorkspaceSearch:focus,
QComboBox#WorkspaceFilter:focus {
    border-color: #3b82f6;
}

QTableWidget#DraftRoomPlayerTable {
    background-color: #0d1421;
    alternate-background-color: #111a29;
    border: 1px solid #243248;
    border-radius: 8px;
    color: #e2e8f0;
    selection-background-color: #173a67;
    selection-color: #ffffff;
    font-size: 10px;
}

QTableWidget#DraftRoomPlayerTable::item {
    border: 0;
    padding: 4px 7px;
}

QTableWidget#DraftRoomPlayerTable::item:selected {
    background-color: #15365f;
    color: #ffffff;
    border-top: 1px solid #2f78c4;
    border-bottom: 1px solid #2f78c4;
    border-left: 2px solid #38bdf8;
}

QTableWidget#DraftRoomPlayerTable::item:hover:!selected {
    background-color: #182438;
    color: #f8fafc;
}

QHeaderView::section {
    background-color: #182235;
    color: #8193ad;
    border: 0;
    border-right: 1px solid #243248;
    border-bottom: 1px solid #243248;
    padding: 6px;
    font-size: 9px;
    font-weight: 900;
}

QLabel#WorkspaceSelection {
    color: #9fb0c7;
    font-size: 10px;
    font-weight: 750;
}

QPushButton#WorkspacePrimaryButton,
QPushButton#WorkspaceSecondaryButton {
    border-radius: 7px;
    padding: 0 12px;
    font-size: 9px;
    font-weight: 950;
}

QPushButton#WorkspacePrimaryButton {
    background-color: #0f6fe8;
    border: 1px solid #2f8cff;
    color: #ffffff;
}

QPushButton#WorkspaceSecondaryButton {
    background-color: #26354a;
    border: 1px solid #3b4d66;
    color: #e2e8f0;
}

QPushButton:disabled {
    background-color: #1b2534;
    border-color: #273548;
    color: #64748b;
}


QLabel#RosterBenchHeader {
    color: #64748b;
    font-size: 8px;
    font-weight: 950;
    letter-spacing: .8px;
    padding-top: 4px;
}

QFrame#RosterSlotRow {
    background-color: #0d1421;
    border: 1px solid #243248;
    border-radius: 6px;
}

QFrame#RosterSlotRow[starter="false"] {
    background-color: #0f1724;
}

QLabel#RosterSlotLabel {
    color: #70829b;
    font-size: 9px;
    font-weight: 950;
}

QLabel#RosterPlayer {
    color: #cbd5e1;
    font-size: 9px;
    font-weight: 800;
}

QLabel#RosterTeam {
    color: #64748b;
    font-size: 8px;
    font-weight: 850;
}





QFrame#GlanceHero {
    background-color: #0c1625;
    border: 1px solid #2b405d;
    border-radius: 11px;
}

QLabel#GlanceMode {
    color: #38bdf8;
    font-size: 8px;
    font-weight: 950;
    letter-spacing: .8px;
}

QLabel#GlanceConfidence {
    color: #91a2b8;
    font-size: 8px;
    font-weight: 900;
}

QLabel#GlancePlayer {
    color: #ffffff;
    font-size: 25px;
    font-weight: 950;
}

QLabel#GlanceMeta {
    color: #8092a9;
    font-size: 8px;
    font-weight: 850;
}

QLabel#GlanceScore {
    color: #ffffff;
    font-size: 17px;
    font-weight: 950;
}

QLabel#GlanceGrade {
    background-color: #172033;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 8px;
    font-weight: 950;
    padding: 4px 7px;
}

QLabel#GlanceReasons {
    color: #e3ebf5;
    font-size: 10px;
    font-weight: 820;
}

QLabel#GlanceAlternatives {
    background-color: #0c1421;
    border: 1px solid #243248;
    border-radius: 8px;
    color: #b7c5d6;
    font-size: 9px;
    font-weight: 820;
    padding: 8px 9px;
}

QToolButton#GlanceMoreButton {
    background-color: #101a2a;
    border: 1px solid #2b3a50;
    border-radius: 8px;
    color: #a9b8ca;
    font-size: 9px;
    font-weight: 900;
    padding: 8px 9px;
    text-align: left;
}

QToolButton#GlanceMoreButton:hover {
    background-color: #162238;
    border-color: #3d5270;
    color: #f8fafc;
}

QToolButton#GlanceMoreButton:checked {
    background-color: #132238;
    border-color: #3b82f6;
    color: #dbeafe;
}

QFrame#GlanceMoreContent {
    background-color: #09111d;
    border: 1px solid #213147;
    border-radius: 8px;
}

QLabel#GlanceAdvancedTitle {
    color: #71839c;
    font-size: 8px;
    font-weight: 950;
    letter-spacing: .6px;
}

QFrame#CoachHero {
    background-color: #0c1625;
    border: 1px solid #2c405c;
    border-radius: 11px;
}

QLabel#CoachEyebrow {
    color: #38bdf8;
    font-size: 8px;
    font-weight: 950;
    letter-spacing: .8px;
}

QLabel#CoachConfidence {
    color: #a8b8cb;
    font-size: 8px;
    font-weight: 900;
}

QLabel#CoachCommand {
    color: #ffffff;
    font-size: 18px;
    font-weight: 950;
}

QLabel#CoachPlayer {
    color: #ffffff;
    font-size: 23px;
    font-weight: 950;
}

QLabel#CoachMeta {
    color: #8495ab;
    font-size: 8px;
    font-weight: 850;
}

QLabel#CoachSummary {
    background-color: #0d1421;
    border-left: 3px solid #38bdf8;
    border-radius: 7px;
    color: #d8e3ef;
    font-size: 10px;
    font-weight: 760;
    padding: 9px 10px;
}

QFrame#CoachSignalCard {
    background-color: #101a2a;
    border: 1px solid #26364d;
    border-radius: 7px;
}

QLabel#CoachSignalTitle {
    color: #64748b;
    font-size: 7px;
    font-weight: 950;
    letter-spacing: .4px;
}

QLabel#CoachSignalValue {
    color: #f8fafc;
    font-size: 11px;
    font-weight: 950;
}

QToolButton#CoachDisclosure {
    background-color: #0d1421;
    border: 1px solid #233249;
    border-radius: 7px;
    color: #aebed1;
    font-size: 9px;
    font-weight: 900;
    padding: 7px 8px;
    text-align: left;
}

QToolButton#CoachDisclosure:hover {
    background-color: #142035;
    border-color: #36506f;
    color: #f1f5f9;
}

QToolButton#CoachDisclosure:checked {
    background-color: #132238;
    border-color: #3b82f6;
    color: #dbeafe;
}

QFrame#CoachAdvancedCard {
    background-color: #0a111d;
    border: 1px solid #223147;
    border-top: 0;
    border-radius: 7px;
}

QLabel#CoachAdvancedText {
    color: #aebed1;
    font-size: 8px;
    font-weight: 800;
}

QLabel#AnalyticsGrade {
    background-color: #172033;
    border: 1px solid #334155;
    border-radius: 7px;
    color: #cbd5e1;
    font-size: 9px;
    font-weight: 950;
    padding: 5px 8px;
    letter-spacing: .4px;
}

QLabel#AnalyticsGrade[strength="elite"] {
    background-color: #123022;
    border-color: #22c55e;
    color: #86efac;
}

QLabel#AnalyticsGrade[strength="strong"] {
    background-color: #12324a;
    border-color: #38bdf8;
    color: #bae6fd;
}

QLabel#AnalyticsGrade[strength="good"] {
    background-color: #3f3510;
    border-color: #eab308;
    color: #fde68a;
}

QLabel#AnalyticsGrade[strength="solid"] {
    background-color: #422d15;
    border-color: #f97316;
    color: #fed7aa;
}

QLabel#AnalyticsGrade[strength="low"] {
    background-color: #40202a;
    border-color: #fb7185;
    color: #fecdd3;
}

QLabel#AnalyticsConfidence {
    color: #71839c;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: .6px;
}



QFrame#DraftTimelineCard {
    background-color: #0c1422;
    border: 1px solid #2b3a50;
    border-radius: 9px;
}

QLabel#DraftTimelineMeta,
QLabel#DraftTimelineSummary {
    color: #8798ae;
    font-size: 8px;
    font-weight: 800;
}

QFrame#DraftTimelineChip {
    background-color: #101a2a;
    border: 1px solid #26364d;
    border-radius: 6px;
    min-width: 42px;
}

QFrame#DraftTimelineChip:hover {
    background-color: #162238;
    border-color: #3d5270;
}

QLabel#DraftTimelinePick {
    color: #73859d;
    font-size: 7px;
    font-weight: 900;
}

QLabel#DraftTimelinePosition {
    font-size: 9px;
    font-weight: 950;
}

QLabel#DraftTimelineProbability {
    color: #cbd5e1;
    font-size: 7px;
    font-weight: 850;
}

QFrame#WaitIntelCard {
    background-color: #0c1422;
    border: 1px solid #2b3a50;
    border-radius: 9px;
}

QLabel#WaitIntelHeadline {
    background-color: #172033;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 8px;
    font-weight: 950;
    padding: 4px 7px;
    letter-spacing: .4px;
}

QLabel#WaitIntelHeadline[risk="high"] {
    background-color: #40202a;
    border-color: #fb7185;
    color: #fecdd3;
}

QLabel#WaitIntelHeadline[risk="medium"] {
    background-color: #422d15;
    border-color: #f59e0b;
    color: #fde68a;
}

QLabel#WaitIntelHeadline[risk="safe"] {
    background-color: #123022;
    border-color: #22c55e;
    color: #86efac;
}

QLabel#WaitIntelWindow {
    color: #71839c;
    font-size: 8px;
    font-weight: 850;
}

QFrame#WaitIntelMetric {
    background-color: #101a2a;
    border: 1px solid #25344a;
    border-radius: 6px;
}

QLabel#WaitIntelMetricTitle {
    color: #64748b;
    font-size: 7px;
    font-weight: 950;
    letter-spacing: .4px;
}

QLabel#WaitIntelMetricValue {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 950;
}

QLabel#WaitIntelDetail {
    color: #8ea0b8;
    font-size: 8px;
    font-weight: 800;
}

QLabel#WaitIntelPath {
    color: #b8c5d6;
    font-size: 8px;
    font-weight: 800;
}

QLabel#AnalyticsPlayer {
    color: #ffffff;
    font-size: 22px;
    font-weight: 950;
}

QFrame#AnalyticsMetricCard {
    background-color: #0d1421;
    border: 1px solid #2b3a50;
    border-radius: 9px;
}

QLabel#AnalyticsMetricTitle {
    color: #70829b;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: .6px;
}

QLabel#AnalyticsMetricValue {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 950;
}

QLabel#AnalyticsAction {
    background-color: #26354a;
    border: 1px solid #3b4d66;
    border-radius: 8px;
    color: #cbd5e1;
    padding: 7px;
    font-size: 11px;
    font-weight: 950;
}

QLabel#AnalyticsAction[action="draft"] {
    background-color: #0b5f3c;
    border-color: #22c55e;
    color: #dcfce7;
}

QLabel#AnalyticsAction[action="risk"] {
    background-color: #6a4319;
    border-color: #f59e0b;
    color: #fef3c7;
}

QLabel#AnalyticsAction[action="wait"] {
    background-color: #173a67;
    border-color: #3b82f6;
    color: #dbeafe;
}

QLabel#AnalyticsSectionTitle {
    color: #8091aa;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: .7px;
}

QLabel#AnalyticsReasons {
    color: #dce6f2;
    font-size: 10px;
    font-weight: 780;
    line-height: 1.35;
}

QLabel#AnalyticsAlternatives {
    background-color: #0d1421;
    border: 1px solid #243248;
    border-radius: 7px;
    color: #aebdd0;
    font-size: 9px;
    font-weight: 800;
    padding: 7px 8px;
}

/* Scrollbars */

QScrollBar:vertical,
QScrollBar:horizontal {
    background-color: #101725;
    border: 0;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background-color: #334155;
    border-radius: 5px;
    min-width: 28px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {
    background-color: #475569;
}

QScrollBar::add-line,
QScrollBar::sub-line {
    width: 0;
    height: 0;
}
"""


class DraftBoardDialog(QDialog):
    """Unified live draft workspace: board above, player browser + AI below."""

    record_player_requested = Signal(str)
    analyze_players_requested = Signal(object)
    undo_requested = Signal()
    redo_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Gridiron AI — Live Draft Room")
        self.resize(1650, 980)
        self.setMinimumSize(1180, 720)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setStyleSheet(DRAFT_BOARD_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setObjectName("DraftRoomMainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(7)

        self.board_host = QWidget()
        board_layout = QVBoxLayout(self.board_host)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.setSpacing(0)

        self.board = DraftBoardWidget(self)
        board_layout.addWidget(self.board)

        self.workspace = DraftRoomWorkspace(self)
        self.workspace.record_requested.connect(self.record_player_requested.emit)
        self.workspace.analyze_requested.connect(self.analyze_players_requested.emit)
        self.workspace.undo_requested.connect(self.undo_requested.emit)
        self.workspace.redo_requested.connect(self.redo_requested.emit)

        # The Draft Room is a separate active window, so the MainWindow QAction
        # does not reliably receive Cmd+Z on macOS. Bind Undo to this window too.
        self.undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        self.undo_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.undo_shortcut.activated.connect(self.undo_requested.emit)

        self.redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        self.redo_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.redo_shortcut.activated.connect(self.redo_requested.emit)

        self.main_splitter.addWidget(self.board_host)
        self.main_splitter.addWidget(self.workspace)
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)
        self.main_splitter.setSizes([580, 360])

        layout.addWidget(self.main_splitter)

    def refresh_board(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
        recommendations=(),
        forecast=None,
        recommendation_mode: str = "auto",
    ) -> None:
        self.board.refresh_board(session, approved_players)
        self.workspace.refresh(
            session=session,
            approved_players=approved_players,
            recommendations=recommendations,
            forecast=forecast,
            recommendation_mode=recommendation_mode,
        )

    def set_analysis_running(self, player_count: int) -> None:
        self.workspace.set_analysis_running(player_count)
