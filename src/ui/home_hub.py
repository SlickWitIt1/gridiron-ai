from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


HUB_STYLESHEET = """
QWidget#HomeHub {
    background-color: #09111d;
}

QLabel#HubBrand {
    color: #f8fafc;
    font-size: 34px;
    font-weight: 950;
}

QLabel#HubTagline {
    color: #8192a9;
    font-size: 13px;
    font-weight: 700;
}

QFrame#HubSetupCard,
QFrame#HubModeCard,
QFrame#HubActiveCard {
    background-color: #0d1624;
    border: 1px solid #25364d;
    border-radius: 13px;
}

QLabel#HubEyebrow {
    color: #38bdf8;
    font-size: 9px;
    font-weight: 950;
    letter-spacing: 1px;
}

QLabel#HubCardTitle {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 950;
}

QLabel#HubBody {
    color: #8ea0b7;
    font-size: 11px;
    font-weight: 700;
}

QLabel#HubFormat {
    color: #aebdd0;
    font-size: 10px;
    font-weight: 800;
}

QComboBox#HubSlot {
    background-color: #101c2c;
    border: 1px solid #334760;
    border-radius: 8px;
    color: #f8fafc;
    font-size: 13px;
    font-weight: 900;
    padding: 8px 10px;
    min-height: 25px;
}

QPushButton#HubLiveButton,
QPushButton#HubMockButton,
QPushButton#HubReturnButton {
    border: 0;
    border-radius: 9px;
    color: white;
    font-size: 12px;
    font-weight: 950;
    padding: 11px 14px;
}

QPushButton#HubLiveButton {
    background-color: #0f766e;
}

QPushButton#HubLiveButton:hover {
    background-color: #0d9488;
}

QPushButton#HubMockButton {
    background-color: #6d28d9;
}

QPushButton#HubMockButton:hover {
    background-color: #7c3aed;
}

QPushButton#HubReturnButton {
    background-color: #2563eb;
}

QPushButton#HubReturnButton:hover {
    background-color: #3b82f6;
}

QPushButton#HubResumeButton {
    background-color: transparent;
    border: 1px solid #334760;
    border-radius: 8px;
    color: #aebdd0;
    font-size: 10px;
    font-weight: 850;
    padding: 8px 11px;
}

QPushButton#HubResumeButton:hover {
    background-color: #142136;
    color: #f8fafc;
}

QPushButton#HubResumeButton:disabled {
    color: #506078;
    border-color: #202e41;
}

QLabel#HubFooter {
    color: #7b8ea7;
    font-size: 13px;
    font-weight: 800;
}

QLabel#HubVersion {
    color: #6f829b;
    font-size: 12px;
    font-weight: 900;
}
"""


class HomeHubWidget(QWidget):
    live_draft_requested = Signal(int)
    mock_draft_requested = Signal(int)
    resume_live_requested = Signal()
    active_draft_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("HomeHub")
        self.setStyleSheet(HUB_STYLESHEET)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 36, 48, 36)
        outer.setSpacing(18)

        outer.addStretch(1)

        brand = QLabel("GRIDIRON AI")
        brand.setObjectName("HubBrand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(brand)

        tagline = QLabel("Draft smarter. One board. One brain.")
        tagline.setObjectName("HubTagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(tagline)

        setup = QFrame()
        setup.setObjectName("HubSetupCard")
        setup_layout = QHBoxLayout(setup)
        setup_layout.setContentsMargins(18, 15, 18, 15)
        setup_layout.setSpacing(14)

        setup_copy = QVBoxLayout()
        setup_copy.setSpacing(3)
        setup_title = QLabel("YOUR DRAFT SLOT")
        setup_title.setObjectName("HubEyebrow")
        setup_copy.addWidget(setup_title)

        fixed = QLabel(
            "10-team snake • Half PPR • 6-pt pass TD • "
            "QB / 2RB / 2WR / TE / FLEX / D/ST / K / 7 Bench"
        )
        fixed.setObjectName("HubFormat")
        fixed.setWordWrap(True)
        setup_copy.addWidget(fixed)
        setup_layout.addLayout(setup_copy, 1)

        self.slot_selector = QComboBox()
        self.slot_selector.setObjectName("HubSlot")
        for slot in range(1, 11):
            self.slot_selector.addItem(f"Slot {slot}", slot)
        self.slot_selector.setCurrentIndex(6)
        setup_layout.addWidget(self.slot_selector)

        outer.addWidget(setup)

        modes = QHBoxLayout()
        modes.setSpacing(14)

        live = self._mode_card(
            eyebrow="REAL DRAFT",
            title="Live Draft",
            body=(
                "Use the Draft Room with friends. You enter every pick as "
                "it happens; Gridiron recommends your selections live."
            ),
            button_text="START LIVE DRAFT",
            button_object="HubLiveButton",
        )
        self.live_button = live.findChild(QPushButton)
        self.live_button.clicked.connect(
            lambda: self.live_draft_requested.emit(self.selected_slot())
        )
        modes.addWidget(live, 1)

        mock = self._mode_card(
            eyebrow="PRACTICE",
            title="Mock Draft",
            body=(
                "Same Draft Room and same Gridiron intelligence. AI controls "
                "the other nine teams and automatically drafts until your turn."
            ),
            button_text="START MOCK DRAFT",
            button_object="HubMockButton",
        )
        self.mock_button = mock.findChild(QPushButton)
        self.mock_button.clicked.connect(
            lambda: self.mock_draft_requested.emit(self.selected_slot())
        )
        modes.addWidget(mock, 1)

        outer.addLayout(modes)

        self.active_card = QFrame()
        self.active_card.setObjectName("HubActiveCard")
        active_layout = QHBoxLayout(self.active_card)
        active_layout.setContentsMargins(16, 12, 16, 12)
        active_layout.setSpacing(12)

        active_copy = QVBoxLayout()
        active_copy.setSpacing(2)

        self.active_title = QLabel("ACTIVE DRAFT")
        self.active_title.setObjectName("HubEyebrow")
        active_copy.addWidget(self.active_title)

        self.active_detail = QLabel("No active draft.")
        self.active_detail.setObjectName("HubBody")
        active_copy.addWidget(self.active_detail)
        active_layout.addLayout(active_copy, 1)

        self.return_button = QPushButton("RETURN TO DRAFT ROOM")
        self.return_button.setObjectName("HubReturnButton")
        self.return_button.clicked.connect(self.active_draft_requested.emit)
        active_layout.addWidget(self.return_button)

        self.active_card.setVisible(False)
        outer.addWidget(self.active_card)

        bottom = QHBoxLayout()
        bottom.addStretch(1)

        self.resume_button = QPushButton("Resume saved Live Draft")
        self.resume_button.setObjectName("HubResumeButton")
        self.resume_button.clicked.connect(self.resume_live_requested.emit)
        bottom.addWidget(self.resume_button)

        bottom.addStretch(1)
        outer.addLayout(bottom)

        note = QLabel(
            "League settings are intentionally fixed for now. "
            "Custom formats can come after the core draft experience is finished."
        )
        note.setObjectName("HubBody")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(note)

        outer.addStretch(1)

        footer = QVBoxLayout()
        footer.setSpacing(2)

        built_by = QLabel("Built by SlickWitIt1")
        built_by.setObjectName("HubFooter")
        built_by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.addWidget(built_by)

        version = QLabel("v0.8.0-alpha")
        version.setObjectName("HubVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.addWidget(version)

        outer.addLayout(footer)

    def _mode_card(
        self,
        *,
        eyebrow: str,
        title: str,
        body: str,
        button_text: str,
        button_object: str,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("HubModeCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 17, 18, 17)
        layout.setSpacing(8)

        label = QLabel(eyebrow)
        label.setObjectName("HubEyebrow")
        layout.addWidget(label)

        heading = QLabel(title)
        heading.setObjectName("HubCardTitle")
        layout.addWidget(heading)

        copy = QLabel(body)
        copy.setObjectName("HubBody")
        copy.setWordWrap(True)
        layout.addWidget(copy)

        layout.addStretch(1)

        button = QPushButton(button_text)
        button.setObjectName(button_object)
        layout.addWidget(button)
        return card

    def selected_slot(self) -> int:
        return int(self.slot_selector.currentData())

    def set_resume_available(self, available: bool) -> None:
        self.resume_button.setEnabled(bool(available))

    def set_active_draft(
        self,
        *,
        mode_name: str | None,
        slot: int | None = None,
        current_pick: int | None = None,
    ) -> None:
        visible = bool(mode_name and slot and current_pick)
        self.active_card.setVisible(visible)
        if not visible:
            return

        self.active_detail.setText(
            f"{mode_name} • Slot {slot} • Overall Pick {current_pick}"
        )
