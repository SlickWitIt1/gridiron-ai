from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout

from live_draft import LiveDraftSession
from ui.draft_board_widget import DraftBoardWidget


DRAFT_BOARD_STYLESHEET = r"""
QDialog {
    background-color: #0b1020;
    color: #f8fafc;
}

QLabel#DraftRoomTitle,
QLabel#DraftRoomSummary,
QLabel#DraftRoomMetaTitle,
QLabel#DraftRoundHeader,
QLabel#DraftRoundLabel,
QLabel#DraftTeamName,
QLabel#DraftCardPick,
QLabel#DraftCardPlayer,
QLabel#DraftCardPosition,
QLabel#DraftCardTeam,
QLabel#DraftCardTeamLogo,
QLabel#DraftCardIntel,
QLabel#DraftRoomLegendText,
QLabel#DraftRoomHoverIntel {
    background-color: transparent;
    border: 0;
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
    letter-spacing: .5px;
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
    letter-spacing: .4px;
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

QLabel#DraftCardIntel {
    color: #e2e8f0;
    font-size: 9px;
    font-weight: 850;
}

QLabel#DraftCardMyGuyBadge {
    background-color: #1f2a3b;
    border: 1px solid #34455e;
    border-radius: 6px;
    color: #facc15;
    font-size: 9px;
    font-weight: 950;
    padding: 2px 5px;
}

QLabel#DraftCardClockBadge {
    background-color: #3a3005;
    border: 1px solid #facc15;
    border-radius: 7px;
    color: #fde047;
    font-size: 8px;
    font-weight: 950;
    letter-spacing: .4px;
    padding: 2px 8px;
}

QFrame#DraftRoomFooter {
    background-color: #101725;
    border: 1px solid #243248;
    border-radius: 10px;
}

QFrame#DraftRoomFooterDivider {
    color: #243248;
    max-width: 1px;
}

QLabel#DraftRoomLegendText {
    color: #8ea0b8;
    font-size: 10px;
    font-weight: 700;
}

QLabel#DraftRoomHoverIntel {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 750;
}

QLabel#DraftRoomHoverIntel[active="true"] {
    color: #e2e8f0;
    font-weight: 850;
}

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
    """Modern card-based draft room while preserving the existing dialog API."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Gridiron AI — Live Draft Room")
        self.resize(1650, 900)
        self.setMinimumSize(1100, 650)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setStyleSheet(DRAFT_BOARD_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.board = DraftBoardWidget(self)
        layout.addWidget(self.board)

    def refresh_board(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
    ) -> None:
        self.board.refresh_board(session, approved_players)
