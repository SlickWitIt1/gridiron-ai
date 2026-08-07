from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from draft_pulse import DraftPulseAnalyzer, DraftPulseSnapshot


POSITION_COLORS = {
    "QB": "#a855f7",
    "RB": "#34d399",
    "WR": "#38bdf8",
    "TE": "#fb923c",
}


class DraftPulseWidget(QWidget):
    def __init__(self, window_size: int = 10) -> None:
        super().__init__()

        self.analyzer = DraftPulseAnalyzer(window_size=window_size)
        self._setup_ui()
        self.reset()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        heading = QLabel("LIVE DRAFT PULSE")
        heading.setObjectName("PanelHeading")
        layout.addWidget(heading)

        self.card = QFrame()
        self.card.setObjectName("DraftPulseCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(5)

        self.headline_label = QLabel("Draft settling in")
        self.headline_label.setObjectName("DraftPulseHeadline")
        self.headline_label.setWordWrap(True)
        card_layout.addWidget(self.headline_label)

        self.detail_label = QLabel(
            "Record a few picks to detect positional runs."
        )
        self.detail_label.setObjectName("DraftPulseDetail")
        self.detail_label.setWordWrap(True)
        card_layout.addWidget(self.detail_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(4)

        self.position_rows: dict[str, tuple[QLabel, QProgressBar]] = {}

        for row, position in enumerate(("RB", "WR", "QB", "TE")):
            label = QLabel(position)
            label.setObjectName("DraftPulsePosition")
            label.setStyleSheet(
                f"color: {POSITION_COLORS[position]}; font-weight: 900;"
            )

            bar = QProgressBar()
            bar.setRange(0, self.analyzer.window_size)
            bar.setTextVisible(True)
            bar.setFormat("0")
            bar.setObjectName("DraftPulseBar")
            bar.setMinimumHeight(17)
            bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

            grid.addWidget(label, row, 0)
            grid.addWidget(bar, row, 1)
            self.position_rows[position] = (label, bar)

        card_layout.addLayout(grid)
        layout.addWidget(self.card)

    def reset(self) -> None:
        self._display_snapshot(
            self.analyzer.analyze(())
        )

    def update_from_session(self, session) -> None:
        if session is None:
            self.reset()
            return

        snapshot = self.analyzer.analyze(
            session.draft_results
        )
        self._display_snapshot(snapshot)

    def _display_snapshot(self, snapshot: DraftPulseSnapshot) -> None:
        self.headline_label.setText(snapshot.headline.upper())
        self.detail_label.setText(snapshot.detail)

        self.card.setProperty(
            "runStrength",
            snapshot.run_strength.lower(),
        )
        self.card.style().unpolish(self.card)
        self.card.style().polish(self.card)

        denominator = max(snapshot.completed_picks, 1)

        for position, (_, bar) in self.position_rows.items():
            count = snapshot.count(position)
            bar.setMaximum(denominator)
            bar.setValue(count)
            bar.setFormat(f"{count} / {snapshot.completed_picks}")
