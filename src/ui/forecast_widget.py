from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout


POSITION_COLORS = {
    "RB": "#34d399",
    "WR": "#38bdf8",
    "QB": "#a855f7",
    "TE": "#fb923c",
}


class ForecastWidget(QFrame):
    """Compact visual summary of the draft forecast before the user's next pick."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ForecastCard")
        self._forecast = None
        self._setup_ui()
        self.reset()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            "QFrame#ForecastCard { background-color: #151b25; border: 1px solid #3b4a60; border-radius: 12px; }"
            "QLabel#ForecastHeadline { color: #f8fafc; font-size: 15px; font-weight: 950; }"
            "QLabel#ForecastMeta { color: #94a3b8; font-size: 11px; }"
            "QLabel#ForecastPosition { font-size: 11px; font-weight: 950; }"
            "QLabel#ForecastValue { color: #e2e8f0; font-size: 11px; font-weight: 900; }"
            "QLabel#ForecastCandidate { background-color: #0f172a; border-radius: 7px; color: #cbd5e1; padding: 8px 10px; font-size: 11px; font-weight: 800; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.headline = QLabel("Forecast waiting")
        self.headline.setObjectName("ForecastHeadline")
        self.run_label = QLabel("—")
        self.run_label.setObjectName("ForecastMeta")
        self.run_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(self.headline, 1)
        top.addWidget(self.run_label)
        layout.addLayout(top)

        self.meta = QLabel("Run an analysis to forecast the picks before your next turn.")
        self.meta.setObjectName("ForecastMeta")
        self.meta.setWordWrap(True)
        layout.addWidget(self.meta)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)
        self.position_rows = {}
        for row, position in enumerate(("WR", "RB", "QB", "TE")):
            label = QLabel(position)
            label.setObjectName("ForecastPosition")
            label.setStyleSheet(f"color: {POSITION_COLORS[position]};")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet(
                "QProgressBar { background-color: #263244; border: 0; border-radius: 5px; }"
                f"QProgressBar::chunk {{ background-color: {POSITION_COLORS[position]}; border-radius: 5px; }}"
            )
            value = QLabel("—")
            value.setObjectName("ForecastValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(label, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)
            self.position_rows[position] = (bar, value)
        layout.addLayout(grid)

        self.candidate = QLabel("Candidate forecast: —")
        self.candidate.setObjectName("ForecastCandidate")
        self.candidate.setWordWrap(True)
        layout.addWidget(self.candidate)

    def reset(self) -> None:
        self._forecast = None
        self.headline.setText("Forecast waiting")
        self.run_label.setText("—")
        self.meta.setText("Run an analysis to forecast the picks before your next turn.")
        for bar, value in self.position_rows.values():
            bar.setValue(0)
            value.setText("—")
        self.candidate.setText("Candidate forecast: —")

    def set_forecast(self, forecast) -> None:
        self._forecast = forecast
        if forecast is None:
            self.reset()
            return

        self.headline.setText(f"NEXT {forecast.picks_between} PICKS")
        if forecast.most_likely_run:
            self.run_label.setText(
                f"{forecast.most_likely_run} run {forecast.run_probability:.0%}"
            )
        else:
            self.run_label.setText("No clear run")
        self.meta.setText(
            f"Forecast through overall pick {forecast.next_user_pick} "
            f"from {forecast.simulations} seeded simulations."
        )

        largest = max(
            (item.expected_picks for item in forecast.position_forecasts),
            default=1.0,
        ) or 1.0
        by_position = {item.position: item for item in forecast.position_forecasts}
        for position, (bar, value) in self.position_rows.items():
            item = by_position.get(position)
            if item is None:
                bar.setValue(0)
                value.setText("0.0")
                continue
            bar.setValue(round(item.expected_picks / largest * 100))
            value.setText(
                f"{item.expected_picks:.1f} exp · {item.run_probability:.0%} run"
            )

    def set_recommendation(self, recommendation) -> None:
        if self._forecast is None or recommendation is None:
            self.candidate.setText("Candidate forecast: —")
            return

        player_forecast = self._forecast.player(recommendation.player_name)
        player_text = (
            f"{player_forecast.survival_probability:.0%} chance available"
            if player_forecast is not None
            else "player survival unavailable"
        )

        tier_forecast = next(
            (
                item
                for item in self._forecast.tier_forecasts
                if item.position == recommendation.position.upper()
                and item.tier_number == recommendation.tier_number
            ),
            None,
        )
        tier_text = (
            f"{tier_forecast.disappearance_probability:.0%} chance "
            f"{tier_forecast.label} disappears"
            if tier_forecast is not None and recommendation.tier_number > 0
            else "tier forecast unavailable"
        )
        self.candidate.setText(
            f"{recommendation.player_name}: {player_text}\n{tier_text}"
        )
