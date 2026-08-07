DARK_STYLESHEET = """
QMainWindow,
QWidget {
    background-color: #111318;
    color: #f2f4f8;
    font-size: 14px;
}

QLabel#TitleLabel {
    font-size: 30px;
    font-weight: 800;
    color: #f8fafc;
    padding: 12px;
}

QLabel#StatusLabel {
    background-color: #1b2028;
    border: 1px solid #313845;
    border-radius: 8px;
    font-size: 17px;
    font-weight: 700;
    padding: 10px;
}

QLabel#PanelHeading {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
    padding-top: 4px;
    padding-bottom: 4px;
}

QLabel#TopPickLabel {
    background-color: #1b2028;
    border: 1px solid #313845;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 700;
    padding: 10px;
}

QLabel#ReasonLabel {
    background-color: #171a20;
    border: 1px solid #313845;
    border-radius: 8px;
    padding: 12px;
}

QLineEdit,
QComboBox,
QSpinBox {
    background-color: #1c2027;
    border: 1px solid #3a4250;
    border-radius: 6px;
    padding: 7px;
    color: #f8fafc;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus {
    border: 1px solid #60a5fa;
}

QListWidget,
QTableWidget {
    background-color: #15181e;
    alternate-background-color: #1a1e25;
    border: 1px solid #313845;
    border-radius: 8px;
    gridline-color: #313845;
    color: #f8fafc;
}

QListWidget::item {
    padding: 7px;
    border-bottom: 1px solid #232933;
}

QListWidget::item:selected,
QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #20252e;
    color: #f8fafc;
    border: 0;
    border-right: 1px solid #313845;
    border-bottom: 1px solid #313845;
    padding: 7px;
    font-weight: 700;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: 0;
    border-radius: 7px;
    padding: 9px 12px;
    font-weight: 700;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #343b47;
    color: #8c95a3;
}

QPushButton#DangerButton {
    background-color: #b91c1c;
}

QPushButton#DangerButton:hover {
    background-color: #dc2626;
}

QPushButton#SecondaryButton {
    background-color: #374151;
}

QPushButton#SecondaryButton:hover {
    background-color: #4b5563;
}

QStatusBar {
    background-color: #171a20;
    color: #cbd5e1;
    border-top: 1px solid #313845;
}
"""

# Ticket 043: Sleeper-inspired command center components.
DARK_STYLESHEET += """
QLabel#CommandCenterHeading {
    font-size: 19px;
    font-weight: 900;
    letter-spacing: 1px;
    color: #f8fafc;
    padding: 2px 0 4px 0;
}

QLabel#CommandCenterStatus {
    color: #94a3b8;
    padding: 2px 0 6px 0;
}

QFrame#HeroCard {
    background-color: #171b23;
    border: 1px solid #354052;
    border-radius: 14px;
}

QLabel#HeroEyebrow {
    color: #facc15;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1px;
}

QLabel#HeroPlayerName {
    color: #ffffff;
    font-size: 27px;
    font-weight: 900;
}

QLabel#HeroMeta {
    color: #a8b3c5;
    font-size: 13px;
    padding-bottom: 5px;
}

QLabel#MetricTitle {
    color: #7f8ca3;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}

QLabel#MetricValue {
    color: #f8fafc;
    font-size: 23px;
    font-weight: 900;
}

QLabel#ConfidenceLabel {
    color: #cbd5e1;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    padding-top: 4px;
}

QProgressBar#ConfidenceBar {
    background-color: #252c38;
    border: 0;
    border-radius: 5px;
    height: 10px;
}

QProgressBar#ConfidenceBar::chunk {
    background-color: #22c55e;
    border-radius: 5px;
}

QLabel#ActionBadge {
    background-color: #334155;
    border-radius: 9px;
    color: #f8fafc;
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 1px;
    padding: 10px;
}

QLabel#ActionBadge[action="draft"] {
    background-color: #166534;
    color: #dcfce7;
}

QLabel#ActionBadge[action="risk"] {
    background-color: #9a3412;
    color: #ffedd5;
}

QLabel#ActionBadge[action="wait"] {
    background-color: #854d0e;
    color: #fef9c3;
}

QLabel#ActionBadge[action="safe"] {
    background-color: #1e40af;
    color: #dbeafe;
}

QFrame#InsightCard {
    background-color: #171b23;
    border: 1px solid #303949;
    border-radius: 10px;
}

QLabel#InsightTitle {
    color: #7f8ca3;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1px;
}

QLabel#InsightValue {
    color: #f8fafc;
    font-size: 13px;
    font-weight: 700;
}

QLabel#SubsectionHeading {
    color: #a8b3c5;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1px;
    padding-top: 5px;
}
"""

# Ticket 044: Draft IQ insight emphasis.
DARK_STYLESHEET += """
QFrame#InsightCard {
    min-height: 58px;
}

QLabel#InsightValue {
    font-size: 13px;
    font-weight: 800;
    color: #e2e8f0;
}
"""

# Ticket 046: Sleeper-inspired War Room shell.
DARK_STYLESHEET += """
QFrame#BrandCard,
QFrame#OnClockCard,
QFrame#DraftProgressCard {
    background-color: #151a22;
    border: 1px solid #2c3645;
    border-radius: 12px;
}

QFrame#BrandCard {
    border-left: 4px solid #3b82f6;
}

QLabel#WarRoomTitle {
    color: #f8fafc;
    font-size: 25px;
    font-weight: 950;
    letter-spacing: 1px;
}

QLabel#WarRoomSubtitle {
    color: #64748b;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}

QFrame#OnClockCard[userTurn="true"] {
    background-color: #132c22;
    border: 1px solid #22c55e;
}

QLabel#OnClockTitle {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 950;
    letter-spacing: .5px;
}

QFrame#OnClockCard[userTurn="true"] QLabel#OnClockTitle {
    color: #86efac;
}

QLabel#OnClockMeta,
QLabel#DraftProgressMeta {
    color: #8492a6;
    font-size: 10px;
    font-weight: 700;
}

QLabel#DraftProgressTitle {
    color: #dbeafe;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .5px;
}

QProgressBar#DraftProgressBar {
    background-color: #232b37;
    border: 0;
    border-radius: 4px;
    height: 8px;
}

QProgressBar#DraftProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 4px;
}

QListWidget::item {
    margin: 2px 4px;
    padding: 8px;
    border: 1px solid transparent;
    border-radius: 6px;
}

QListWidget::item:hover {
    background-color: #202733;
    border-color: #334155;
}

QListWidget::item:selected {
    background-color: #1d4ed8;
    border-color: #60a5fa;
    color: #ffffff;
}

QLabel#PanelHeading {
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 1px;
    text-transform: uppercase;
}
"""

# Ticket 051: compact live draft pulse.
DARK_STYLESHEET += """
QFrame#DraftPulseCard {
    background-color: #171b23;
    border: 1px solid #303949;
    border-radius: 10px;
}

QFrame#DraftPulseCard[runStrength="watch"] {
    border: 1px solid #facc15;
}

QFrame#DraftPulseCard[runStrength="active"] {
    border: 1px solid #fb923c;
}

QFrame#DraftPulseCard[runStrength="strong"] {
    border: 1px solid #ef4444;
}

QLabel#DraftPulseHeadline {
    color: #f8fafc;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.5px;
}

QLabel#DraftPulseDetail {
    color: #94a3b8;
    font-size: 11px;
}

QLabel#DraftPulsePosition {
    min-width: 24px;
    font-size: 11px;
}

QProgressBar#DraftPulseBar {
    background-color: #252c38;
    border: 0;
    border-radius: 5px;
    color: #f8fafc;
    font-size: 10px;
    font-weight: 800;
    text-align: center;
}

QProgressBar#DraftPulseBar::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}
"""

# Ticket 054: command-center-first layout and aligned player rows.
DARK_STYLESHEET += """
QLineEdit {
    min-height: 24px;
    padding: 8px 10px;
}


QFrame#CostOfPassingCard {
    background-color: #151b25;
    border: 1px solid #3b4a60;
    border-radius: 13px;
}

QLabel#CostHeadline {
    color: #f8fafc;
    font-size: 19px;
    font-weight: 950;
    letter-spacing: .4px;
    padding: 2px 0 4px 0;
}

QLabel#CostHeadline[state="take"] {
    color: #4ade80;
}

QLabel#CostHeadline[state="pass"] {
    color: #fbbf24;
}

QFrame#PathCard {
    background-color: #101722;
    border: 1px solid #334155;
    border-radius: 10px;
}

QFrame#PathCard[pathType="take"] {
    border-left: 5px solid #22c55e;
}

QFrame#PathCard[pathType="pass"] {
    border-left: 5px solid #f59e0b;
}

QLabel#PathTitle {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 950;
    letter-spacing: 1px;
}

QLabel#PathPlayer {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 850;
}

QLabel#PathArrow {
    color: #64748b;
    font-size: 15px;
    font-weight: 900;
}

QLabel#TierRiskLabel {
    background-color: #0f172a;
    border-radius: 7px;
    color: #fca5a5;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .5px;
    padding: 8px 10px;
}
"""

# Ticket 055: true resizable war-room shell and custom player rows.
DARK_STYLESHEET += """
QSplitter#WarRoomSplitter::handle {
    background-color: #202733;
    border-radius: 3px;
    margin: 4px 1px;
}

QSplitter#WarRoomSplitter::handle:hover {
    background-color: #3b82f6;
}

QWidget#LeftPanel,
QWidget#MiddlePanel,
QWidget#RightPanel {
    background-color: transparent;
}

QListWidget#AvailablePlayersList {
    outline: 0;
    padding: 3px;
}

QListWidget#AvailablePlayersList::item {
    background-color: transparent;
    border: 0;
    margin: 1px 0;
    padding: 0;
}

QListWidget#AvailablePlayersList::item:hover,
QListWidget#AvailablePlayersList::item:selected {
    background-color: transparent;
    border: 0;
}

"""


# Ticket 055A: lightweight available-player rows.
DARK_STYLESHEET += """
QListWidget#AvailablePlayersList {
    background-color: #15181e;
    border: 1px solid #313845;
    border-radius: 8px;
    outline: 0;
}

QListWidget#AvailablePlayersList::item {
    margin: 1px 4px;
    padding: 6px 8px;
    border: 1px solid transparent;
    border-radius: 6px;
}

QListWidget#AvailablePlayersList::item:hover {
    background-color: #202733;
    border-color: #334155;
}

QListWidget#AvailablePlayersList::item:selected {
    background-color: #172554;
    border-color: #3b82f6;
    color: #ffffff;
}
"""


# Ticket 057: control sizing, native dropdown arrows, and left-panel balance.
DARK_STYLESHEET += """
QLabel#AvailablePlayersHeader {
    background-color: #1c222c;
    border: 1px solid #313845;
    border-bottom: 0;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: .4px;
    padding: 6px 10px;
}

QListWidget#AvailablePlayersList {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
}

/* Keep the native macOS/Qt arrow visible. */
QComboBox#PositionFilter {
    min-width: 112px;
    padding: 5px 10px;
}

QComboBox#LeftControl {
    padding: 4px 10px;
}

QSpinBox#LeftControl {
    padding: 4px 28px 4px 10px;
}

QWidget#LeftPanel QLabel {
    padding-left: 3px;
    padding-right: 3px;
}

QWidget#LeftPanel QPushButton {
    padding: 6px 10px;
}

QLabel#PlayerLegend {
    color: #cbd5e1;
    padding: 2px 1px 0 1px;
}

QFrame#DraftPulseCard {
    margin-right: 2px;
}
"""


# Ticket 057A: compact actions and unclipped left controls.
DARK_STYLESHEET += """
QComboBox#LeftControl,
QSpinBox#LeftControl {
    min-height: 28px;
    padding-top: 2px;
    padding-bottom: 2px;
}

QSpinBox#LeftControl {
    padding-left: 10px;
    padding-right: 30px;
}

QWidget#LeftPanel QPushButton {
    min-height: 0;
    padding: 3px 10px;
    font-size: 13px;
}
"""
