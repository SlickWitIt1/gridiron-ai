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
