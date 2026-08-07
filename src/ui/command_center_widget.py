from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


POSITION_COLORS = {
    "QB": "#a855f7",
    "RB": "#34d399",
    "WR": "#38bdf8",
    "TE": "#fb923c",
    "DST": "#94a3b8",
    "K": "#facc15",
}


INSIGHTS = {
    "DECISION SCORE": (
        "The overall recommendation score out of 100. It combines projection, "
        "wait risk, roster fit, scarcity, tier value, opportunity cost, strategy "
        "fit, and My Guy preference."
    ),
    "RATING": (
        "A letter grade derived from the Decision Score. It summarizes the "
        "strength of this recommendation, not the player's real-life talent."
    ),
    "SURVIVES": (
        "Estimated probability that this player remains available at your next pick."
    ),
    "CONFIDENCE": (
        "How strongly the available evidence supports this recommendation. Higher "
        "confidence means the score, wait signal, tier signal, and other factors "
        "point more clearly in the same direction."
    ),
    "CURRENT BUILD": (
        "The draft strategy detected from your actual picks, their rounds, and player "
        "quality. The build can change as your draft develops."
    ),
    "STRATEGY CONFIDENCE": (
        "How clearly the detected primary strategy leads the next-best strategy."
    ),
    "SECONDARY STRATEGY": (
        "The second-most likely interpretation of your current draft structure."
    ),
    "NEXT PRIORITIES": (
        "Suggested ways to continue the detected build. These are guidance, not rigid rules."
    ),
    "COST OF PASSING": (
        "Compares two simulated roster paths: taking this player now versus passing "
        "and drafting the most likely alternatives across your next two selections."
    ),
    "TAKE PATH": (
        "The most common two-pick roster path when you draft this player now."
    ),
    "PASS PATH": (
        "The most common two-pick roster path when you pass on this player now."
    ),
    "TIER DISAPPEARANCE": (
        "Estimated probability that every currently available player in this player's "
        "tier is gone by your next pick."
    ),
    "WAIT RISK": (
        "Rewards players who are unlikely to survive until your next selection."
    ),
    "ROSTER NEED": (
        "How well the player's position fills an open starter, FLEX, or depth need, "
        "including penalties for redundant positions."
    ),
    "TIER STATUS": (
        "Shows the player's projection-based tier, how many players remain in it, "
        "and the projected drop to the next tier."
    ),
    "PROJECTION": (
        "Value above the replacement-level projection for this position."
    ),
    "ROSTER FIT": (
        "Score for positional need, starter/FLEX fit, depth, and roster redundancy."
    ),
    "SCARCITY": (
        "How scarce comparable options are, using tier urgency and the positional drop-off."
    ),
    "TIER DROP": (
        "Points awarded for the projected scoring cliff between this tier and the next tier."
    ),
    "OPPORTUNITY COST": (
        "Score derived from how much better the simulated take-now roster path performs "
        "than the simulated pass path."
    ),
    "STRATEGY FIT": (
        "How well this candidate continues your detected draft build. Strong tier value "
        "can still justify an exception."
    ),
    "MY GUY": (
        "A small preference bonus when the player is on your My Guys list."
    ),
    "TOP ALTERNATIVES": (
        "Other analyzed candidates, kept in the exact order produced by the recommendation engine."
    ),
    "ACTION": (
        "Plain-language recommendation based primarily on the player's chance to survive "
        "until your next pick."
    ),
}


class CommandCenterWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.current_recommendations = []
        self.breakdown_rows = {}
        self.alternative_buttons: list[QPushButton] = []
        self._insight_targets: dict[object, str] = {}
        self._insight_pinned_key: str | None = None
        self._insight_active_key = "DECISION SCORE"
        self._live_insight_title = "READY FOR ANALYSIS"
        self._live_insight_body = (
            "Select players and run an analysis. The strongest recommendation "
            "and its clearest reasons will appear here automatically."
        )
        self._setup_ui()
        self.reset()

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(10)

        heading = QLabel("DRAFT IQ COMMAND CENTER")
        heading.setObjectName("CommandCenterHeading")
        layout.addWidget(heading)

        self.status_label = QLabel(
            "Select players and click Analyze Selected."
        )
        self.status_label.setObjectName("CommandCenterStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.hero_card = QFrame()
        self.hero_card.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(18, 16, 18, 16)
        hero_layout.setSpacing(8)

        eyebrow = QLabel("★ RECOMMENDED PICK")
        eyebrow.setObjectName("HeroEyebrow")
        hero_layout.addWidget(eyebrow)

        name_row = QHBoxLayout()
        self.player_name_label = QLabel("Waiting for analysis")
        self.player_name_label.setObjectName("HeroPlayerName")
        self.player_name_label.setStyleSheet(
            "font-size: 34px; font-weight: 900; padding: 4px 0;"
        )
        name_row.addWidget(self.player_name_label, 1)

        self.position_badge = QLabel("—")
        self.position_badge.setObjectName("PositionBadge")
        self.position_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_badge.setMinimumWidth(56)
        name_row.addWidget(self.position_badge)
        hero_layout.addLayout(name_row)

        self.player_meta_label = QLabel(
            "Select candidates to generate a recommendation."
        )
        self.player_meta_label.setObjectName("HeroMeta")
        hero_layout.addWidget(self.player_meta_label)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(4)

        metrics.addWidget(self._metric_title("DECISION SCORE"), 0, 0)
        metrics.addWidget(self._metric_title("RATING"), 0, 1)
        metrics.addWidget(self._metric_title("SURVIVES"), 0, 2)

        self.score_label = self._metric_value("—")
        self.grade_label = self._metric_value("—")
        self.survival_label = self._metric_value("—")

        metrics.addWidget(self.score_label, 1, 0)
        metrics.addWidget(self.grade_label, 1, 1)
        metrics.addWidget(self.survival_label, 1, 2)
        hero_layout.addLayout(metrics)

        self.confidence_label = QLabel("CONFIDENCE —")
        self.confidence_label.setObjectName("ConfidenceLabel")
        self._register_insight(self.confidence_label, "CONFIDENCE")
        hero_layout.addWidget(self.confidence_label)

        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setObjectName("ConfidenceBar")
        self.confidence_bar.setMinimumHeight(22)
        self._register_insight(self.confidence_bar, "CONFIDENCE")
        hero_layout.addWidget(self.confidence_bar)

        self.action_label = QLabel("ANALYZE PLAYERS")
        self.action_label.setObjectName("ActionBadge")
        self.action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_label.setMinimumHeight(46)
        self._register_insight(self.action_label, "ACTION")
        self.action_label.setStyleSheet(
            "font-size: 17px; font-weight: 900; border-radius: 10px;"
        )
        hero_layout.addWidget(self.action_label)

        layout.addWidget(self.hero_card)

        # Keep the contextual insight directly below the recommendation so it
        # remains visible while the user explores the most important metrics.
        insight_heading = QLabel("AI DRAFT INSIGHT")
        insight_heading.setObjectName("SubsectionHeading")
        layout.addWidget(insight_heading)

        self.insight_panel = QFrame()
        self.insight_panel.setObjectName("GridironInsightPanel")
        self.insight_panel.setStyleSheet(
            "QFrame#GridironInsightPanel { background-color: #101722; "
            "border: 1px solid #3b4a60; border-left: 4px solid #facc15; "
            "border-radius: 12px; }"
            "QLabel#GridironInsightMetric { color: #f8fafc; font-size: 14px; "
            "font-weight: 950; }"
            "QLabel#GridironInsightStatus { color: #4ade80; font-size: 9px; "
            "font-weight: 950; letter-spacing: 1px; }"
            "QLabel#GridironInsightBody { color: #cbd5e1; font-size: 12px; "
            "line-height: 1.35; }"
            "QLabel#GridironInsightHint { color: #64748b; font-size: 10px; }"
        )
        insight_layout = QVBoxLayout(self.insight_panel)
        insight_layout.setContentsMargins(14, 12, 14, 12)
        insight_layout.setSpacing(5)

        insight_top_row = QHBoxLayout()
        self.insight_metric_label = QLabel(self._live_insight_title)
        self.insight_metric_label.setObjectName("GridironInsightMetric")
        self.insight_status_label = QLabel("LIVE")
        self.insight_status_label.setObjectName("GridironInsightStatus")
        self.insight_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        insight_top_row.addWidget(self.insight_metric_label, 1)
        insight_top_row.addWidget(self.insight_status_label)
        insight_layout.addLayout(insight_top_row)

        self.insight_body_label = QLabel(self._live_insight_body)
        self.insight_body_label.setObjectName("GridironInsightBody")
        self.insight_body_label.setWordWrap(True)
        self.insight_body_label.setMinimumHeight(42)
        self.insight_body_label.setMaximumHeight(120)
        insight_layout.addWidget(self.insight_body_label)

        self.insight_hint_label = QLabel(
            "Hover for help • Click to pin • Click the pinned item again to return live"
        )
        self.insight_hint_label.setObjectName("GridironInsightHint")
        self.insight_hint_label.setWordWrap(True)
        insight_layout.addWidget(self.insight_hint_label)
        layout.addWidget(self.insight_panel)

        strategy_heading = QLabel("CURRENT BUILD")
        strategy_heading.setObjectName("SubsectionHeading")
        self._register_insight(strategy_heading, "CURRENT BUILD")
        layout.addWidget(strategy_heading)

        self.strategy_card = QFrame()
        self.strategy_card.setObjectName("InsightCard")
        self._register_insight(self.strategy_card, "CURRENT BUILD")
        self.strategy_card.setStyleSheet(
            "QFrame#InsightCard {"
            "background-color: #151b25;"
            "border: 1px solid #3b4a60;"
            "border-radius: 12px;"
            "}"
        )
        strategy_layout = QGridLayout(self.strategy_card)
        strategy_layout.setContentsMargins(14, 12, 14, 12)
        strategy_layout.setHorizontalSpacing(16)
        strategy_layout.setVerticalSpacing(5)

        self.strategy_name_label = QLabel("Still learning")
        self._register_insight(self.strategy_name_label, "CURRENT BUILD")
        self.strategy_name_label.setStyleSheet(
            "font-size: 19px; font-weight: 950; color: #f8fafc;"
        )
        self.strategy_confidence_label = QLabel("0% confidence")
        self.strategy_confidence_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._register_insight(self.strategy_confidence_label, "STRATEGY CONFIDENCE")
        self.strategy_confidence_label.setStyleSheet(
            "font-size: 12px; font-weight: 900; color: #93c5fd;"
        )
        self.strategy_secondary_label = QLabel("Secondary: —")
        self._register_insight(self.strategy_secondary_label, "SECONDARY STRATEGY")
        self.strategy_secondary_label.setStyleSheet(
            "font-size: 12px; color: #94a3b8;"
        )
        self.strategy_priority_label = QLabel("Next: Best Value")
        self.strategy_priority_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.strategy_priority_label.setWordWrap(True)
        self._register_insight(self.strategy_priority_label, "NEXT PRIORITIES")
        self.strategy_priority_label.setStyleSheet(
            "font-size: 12px; font-weight: 800; color: #cbd5e1;"
        )

        strategy_layout.addWidget(self.strategy_name_label, 0, 0)
        strategy_layout.addWidget(self.strategy_confidence_label, 0, 1)
        strategy_layout.addWidget(self.strategy_secondary_label, 1, 0)
        strategy_layout.addWidget(self.strategy_priority_label, 1, 1)
        layout.addWidget(self.strategy_card)

        cost_heading = QLabel("COST OF PASSING")
        cost_heading.setObjectName("SubsectionHeading")
        self._register_insight(cost_heading, "COST OF PASSING")
        layout.addWidget(cost_heading)

        self.cost_card = QFrame()
        self.cost_card.setObjectName("CostOfPassingCard")
        self._register_insight(self.cost_card, "COST OF PASSING")
        cost_layout = QVBoxLayout(self.cost_card)
        cost_layout.setContentsMargins(16, 14, 16, 14)
        cost_layout.setSpacing(10)

        self.cost_headline_label = QLabel("Run an analysis to compare roster paths.")
        self.cost_headline_label.setObjectName("CostHeadline")
        self.cost_headline_label.setWordWrap(True)
        self._register_insight(self.cost_headline_label, "COST OF PASSING")
        cost_layout.addWidget(self.cost_headline_label)

        path_grid = QGridLayout()
        path_grid.setSpacing(10)

        self.take_path_frame = self._path_card("TAKE NOW", "—", "—", "take")
        self._register_insight(self.take_path_frame, "TAKE PATH")
        self.pass_path_frame = self._path_card("PASS", "—", "—", "pass")
        self._register_insight(self.pass_path_frame, "PASS PATH")
        path_grid.addWidget(self.take_path_frame, 0, 0)
        path_grid.addWidget(self.pass_path_frame, 0, 1)
        cost_layout.addLayout(path_grid)

        self.tier_risk_label = QLabel("Tier disappearance risk: —")
        self.tier_risk_label.setObjectName("TierRiskLabel")
        self._register_insight(self.tier_risk_label, "TIER DISAPPEARANCE")
        cost_layout.addWidget(self.tier_risk_label)

        layout.addWidget(self.cost_card)

        evidence_grid = QGridLayout()
        evidence_grid.setSpacing(8)

        self.wait_risk_card = self._small_card(
            "WAIT RISK", "No analysis yet"
        )
        self.roster_fit_card = self._small_card(
            "ROSTER NEED", "No analysis yet"
        )
        self.tier_drop_card = self._small_card(
            "TIER STATUS", "No analysis yet"
        )

        evidence_grid.addWidget(self.wait_risk_card, 0, 0)
        evidence_grid.addWidget(self.roster_fit_card, 0, 1)
        evidence_grid.addWidget(self.tier_drop_card, 0, 2)
        layout.addLayout(evidence_grid)

        breakdown_heading = QLabel("SCORE BREAKDOWN")
        breakdown_heading.setObjectName("SubsectionHeading")
        layout.addWidget(breakdown_heading)

        self.breakdown_frame = QFrame()
        self.breakdown_frame.setObjectName("InsightCard")
        self.breakdown_frame.setMinimumHeight(250)
        breakdown_layout = QVBoxLayout(self.breakdown_frame)
        breakdown_layout.setContentsMargins(12, 10, 12, 10)
        breakdown_layout.setSpacing(8)

        component_names = (
            "Projection",
            "Wait Risk",
            "Roster Fit",
            "Scarcity",
            "Tier Drop",
            "Opportunity Cost",
            "Strategy Fit",
            "My Guy",
        )

        for component_name in component_names:
            component_row = QFrame()
            component_row.setStyleSheet(
                "QFrame {"
                "background-color: #10151d;"
                "border: 1px solid #283446;"
                "border-radius: 8px;"
                "}"
            )
            component_layout = QVBoxLayout(component_row)
            component_layout.setContentsMargins(10, 7, 10, 7)
            component_layout.setSpacing(5)

            header_row = QHBoxLayout()
            name_label = QLabel(component_name.upper())
            self._register_insight(component_row, component_name.upper())
            self._register_insight(name_label, component_name.upper())
            name_label.setStyleSheet(
                "font-size: 11px; font-weight: 900; color: #cbd5e1;"
            )
            value_label = QLabel("—")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setStyleSheet(
                "font-size: 12px; font-weight: 900; color: #f8fafc;"
            )
            header_row.addWidget(name_label, 1)
            header_row.addWidget(value_label)
            component_layout.addLayout(header_row)

            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setTextVisible(False)
            progress_bar.setMinimumHeight(11)
            progress_bar.setMaximumHeight(11)
            progress_bar.setStyleSheet(
                "QProgressBar {"
                "background-color: #263244;"
                "border: 0;"
                "border-radius: 5px;"
                "}"
                "QProgressBar::chunk {"
                "background-color: #22c55e;"
                "border-radius: 5px;"
                "}"
            )
            component_layout.addWidget(progress_bar)

            breakdown_layout.addWidget(component_row)
            self.breakdown_rows[component_name] = (
                progress_bar,
                value_label,
            )

        layout.addWidget(self.breakdown_frame)

        alternatives = QLabel("TOP ALTERNATIVES")
        alternatives.setObjectName("SubsectionHeading")
        self._register_insight(alternatives, "TOP ALTERNATIVES")
        layout.addWidget(alternatives)

        self.alternatives_frame = QFrame()
        self.alternatives_frame.setObjectName("InsightCard")
        self.alternatives_frame.setMinimumHeight(92)
        self.alternatives_layout = QVBoxLayout(self.alternatives_frame)
        self.alternatives_layout.setContentsMargins(8, 8, 8, 8)
        self.alternatives_layout.setSpacing(7)

        self.no_alternatives_label = QLabel(
            "Analyze more than one player to see alternatives."
        )
        self.no_alternatives_label.setWordWrap(True)
        self.no_alternatives_label.setStyleSheet(
            "color: #94a3b8; padding: 8px;"
        )
        self.alternatives_layout.addWidget(self.no_alternatives_label)
        layout.addWidget(self.alternatives_frame)

        # Kept as a hidden compatibility table because main_window.py still
        # references command_center.table. Visible alternatives are cards.
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            (
                "Rank",
                "Player",
                "Pos",
                "Score",
                "Grade",
                "Survives",
                "EV Lost",
                "Action",
            )
        )
        self.table.setSortingEnabled(False)
        self.table.hide()

        why = QLabel("WHY THIS PICK?")
        why.setObjectName("SubsectionHeading")
        layout.addWidget(why)

        self.reason_label = QLabel(
            "Recommendation details will appear here."
        )
        self.reason_label.setObjectName("ReasonLabel")
        self.reason_label.setWordWrap(True)
        self.reason_label.setMinimumHeight(108)
        layout.addWidget(self.reason_label)

        layout.addStretch()

        self.scroll_area.setWidget(content)
        outer_layout.addWidget(self.scroll_area)

    def _metric_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("MetricTitle")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._register_insight(label, text)
        return label

    @staticmethod
    def _metric_value(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("MetricValue")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    @staticmethod
    def _path_card(
        title: str,
        first_player: str,
        second_player: str,
        path_type: str,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("PathCard")
        frame.setProperty("pathType", path_type)
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("PathTitle")
        first_label = QLabel(first_player)
        first_label.setObjectName("PathPlayer")
        arrow_label = QLabel("↓")
        arrow_label.setObjectName("PathArrow")
        second_label = QLabel(second_player)
        second_label.setObjectName("PathPlayer")

        card_layout.addWidget(title_label)
        card_layout.addWidget(first_label)
        card_layout.addWidget(arrow_label)
        card_layout.addWidget(second_label)

        frame.first_player_label = first_label
        frame.second_player_label = second_label
        return frame

    def _small_card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("InsightCard")
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(12, 10, 12, 10)

        title_label = QLabel(title)
        title_label.setObjectName("InsightTitle")
        self._register_insight(frame, title)
        self._register_insight(title_label, title)
        value_label = QLabel(value)
        self._register_insight(value_label, title)
        value_label.setObjectName("InsightValue")
        value_label.setWordWrap(True)

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        frame.value_label = value_label
        return frame

    def _register_insight(self, widget: QWidget, key: str) -> None:
        """Connect one UI element to the fixed insight panel."""
        if key not in INSIGHTS:
            return
        widget.setMouseTracking(True)
        widget.installEventFilter(self)
        self._insight_targets[widget] = key

    def _render_insight(self, title: str, body: str, status: str) -> None:
        self.insight_metric_label.setText(title)
        self.insight_body_label.setText(body)
        self.insight_status_label.setText(status)

    def _set_live_insight(self, title: str, body: str) -> None:
        self._live_insight_title = title
        self._live_insight_body = body
        if self._insight_pinned_key is None:
            self._render_insight(title, body, "LIVE")

    def _restore_live_insight(self) -> None:
        if self._insight_pinned_key is None:
            self._render_insight(
                self._live_insight_title,
                self._live_insight_body,
                "LIVE",
            )

    def _show_insight(self, key: str, pinned: bool | None = None) -> None:
        if key not in INSIGHTS:
            return
        self._insight_active_key = key
        if pinned is True:
            self._insight_pinned_key = key
        elif pinned is False:
            self._insight_pinned_key = None

        if self._insight_pinned_key is None and pinned is False:
            self._restore_live_insight()
            return

        status = "PINNED" if self._insight_pinned_key else "EXPLAINING"
        self._render_insight(key, INSIGHTS[key], status)

    def eventFilter(self, watched, event) -> bool:
        key = self._insight_targets.get(watched)
        if key is not None:
            if event.type() == QEvent.Type.Enter and self._insight_pinned_key is None:
                self._show_insight(key)
            elif event.type() == QEvent.Type.Leave and self._insight_pinned_key is None:
                self._restore_live_insight()
            elif event.type() == QEvent.Type.MouseButtonPress:
                if self._insight_pinned_key == key:
                    self._show_insight(key, pinned=False)
                else:
                    self._show_insight(key, pinned=True)
        return super().eventFilter(watched, event)

    def reset(self) -> None:
        self.current_recommendations = []
        self._insight_pinned_key = None
        self._set_live_insight(
            "READY FOR ANALYSIS",
            "Select players and run an analysis. The strongest recommendation "
            "and its clearest reasons will appear here automatically.",
        )
        self.status_label.setText(
            "Select players and click Analyze Selected."
        )
        self.player_name_label.setText("Waiting for analysis")
        self.player_meta_label.setText(
            "Select candidates to generate a recommendation."
        )
        self.position_badge.setText("—")
        self.position_badge.setStyleSheet("")
        self.score_label.setText("—")
        self.grade_label.setText("—")
        self.grade_label.setStyleSheet("")
        self.survival_label.setText("—")
        self.confidence_label.setText("CONFIDENCE —")
        self.confidence_bar.setValue(0)
        self.action_label.setText("ANALYZE PLAYERS")
        self.action_label.setProperty("action", "neutral")
        self.action_label.style().unpolish(self.action_label)
        self.action_label.style().polish(self.action_label)
        self.strategy_name_label.setText("Still learning")
        self.strategy_confidence_label.setText("0% confidence")
        self.strategy_secondary_label.setText("Secondary: —")
        self.strategy_priority_label.setText("Next: Best Value")
        self.wait_risk_card.value_label.setText("No analysis yet")
        self.roster_fit_card.value_label.setText("No analysis yet")
        self.tier_drop_card.value_label.setText("No analysis yet")
        self.cost_headline_label.setText(
            "Run an analysis to compare roster paths."
        )
        self.take_path_frame.first_player_label.setText("—")
        self.take_path_frame.second_player_label.setText("—")
        self.pass_path_frame.first_player_label.setText("—")
        self.pass_path_frame.second_player_label.setText("—")
        self.tier_risk_label.setText("Tier disappearance risk: —")

        for progress_bar, value_label in self.breakdown_rows.values():
            progress_bar.setValue(0)
            value_label.setText("—")

        self._clear_alternative_cards()
        self.no_alternatives_label.show()

        self.reason_label.setText(
            "Recommendation details will appear here."
        )
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

    def set_running(self, simulations: int, player_count: int) -> None:
        self.status_label.setText(
            f"Running {simulations} simulations for "
            f"{player_count} players..."
        )
        self.action_label.setText("ANALYZING...")
        self.action_label.setProperty("action", "neutral")
        self.action_label.style().unpolish(self.action_label)
        self.action_label.style().polish(self.action_label)

    def set_results(self, recommendations, runtime: float) -> None:
        self.current_recommendations = list(recommendations)
        self.status_label.setText(
            f"Analysis completed in {runtime:.1f} seconds."
        )

        # Preserve the engine's ranking exactly. Sorting remains disabled so
        # Rank 1 can never be moved below Rank 2 by Qt's table sorting state.
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(recommendations))

        for row, recommendation in enumerate(recommendations):
            survival_text = (
                f"{recommendation.survival_probability:.1%}"
                if recommendation.survival_probability is not None
                else "N/A"
            )
            values = (
                str(row + 1),
                recommendation.player_name,
                recommendation.position,
                f"{recommendation.score:.1f}",
                recommendation.grade,
                survival_text,
                f"{recommendation.expected_value_lost:.1f}",
                recommendation.action,
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in {0, 2, 3, 4, 5, 6}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._apply_table_color(
                    item,
                    column,
                    recommendation.grade,
                    recommendation.action,
                    recommendation.position,
                )
                self.table.setItem(row, column, item)

        self._populate_alternative_cards()

        if recommendations:
            self.display_recommendation(recommendations[0])
            self.table.selectRow(0)
        else:
            self.reset()
            self.status_label.setText("No recommendations were produced.")

    def _populate_alternative_cards(self) -> None:
        self._clear_alternative_cards()

        alternatives = self.current_recommendations[1:4]
        if not alternatives:
            self.no_alternatives_label.show()
            return

        self.no_alternatives_label.hide()

        for rank, recommendation in enumerate(alternatives, start=2):
            position = recommendation.position.upper()
            position_color = POSITION_COLORS.get(position, "#94a3b8")
            survival_text = (
                f"{recommendation.survival_probability:.0%} survives"
                if recommendation.survival_probability is not None
                else "Usually gone"
            )

            button = QPushButton()
            self._register_insight(button, "TOP ALTERNATIVES")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            button.setMinimumHeight(64)
            tier_text = (
                f"Tier {recommendation.tier_number} · "
                f"{recommendation.players_remaining_in_tier} left"
                if recommendation.tier_number > 0
                else "Tier unavailable"
            )
            button.setText(
                f"#{rank}  {recommendation.player_name}   "
                f"{position}\n"
                f"{recommendation.score:.0f}/100  •  "
                f"{recommendation.grade}  •  {tier_text}  •  "
                f"{survival_text}  •  "
                f"Cost {recommendation.opportunity_cost:+.1f}  •  "
                f"{recommendation.action}"
            )
            button.setStyleSheet(
                "QPushButton {"
                "text-align: left;"
                "background-color: #111827;"
                "border: 1px solid #334155;"
                f"border-left: 5px solid {position_color};"
                "border-radius: 9px;"
                "padding: 8px 12px;"
                "font-size: 12px;"
                "font-weight: 800;"
                "color: #f8fafc;"
                "}"
                "QPushButton:hover {"
                "background-color: #172033;"
                "border-color: #60a5fa;"
                "}"
                "QPushButton:pressed {"
                "background-color: #0f172a;"
                "}"
            )
            button.clicked.connect(
                lambda checked=False, rec=recommendation: (
                    self._select_alternative(rec)
                )
            )
            self.alternatives_layout.addWidget(button)
            self.alternative_buttons.append(button)

        self.alternatives_frame.setMinimumHeight(
            18 + (len(self.alternative_buttons) * 71)
        )

    def _select_alternative(self, recommendation) -> None:
        self.display_recommendation(recommendation)

        for row in range(self.table.rowCount()):
            player_item = self.table.item(row, 1)
            if (
                player_item is not None
                and player_item.text() == recommendation.player_name
            ):
                self.table.selectRow(row)
                break

    def _clear_alternative_cards(self) -> None:
        for button in self.alternative_buttons:
            self.alternatives_layout.removeWidget(button)
            button.deleteLater()
        self.alternative_buttons = []
        self.alternatives_frame.setMinimumHeight(92)

    def display_recommendation(self, recommendation) -> None:
        position = recommendation.position.upper()
        survival = recommendation.survival_probability
        survival_text = (
            f"{survival:.1%}" if survival is not None else "N/A"
        )

        self.player_name_label.setText(recommendation.player_name)
        tier_meta = (
            f"  •  TIER {recommendation.tier_number}"
            f"  •  {recommendation.players_remaining_in_tier} LEFT"
            if recommendation.tier_number > 0
            else ""
        )
        self.player_meta_label.setText(
            f"{position}  •  {recommendation.projected_points:.1f} projected pts"
            + tier_meta
            + ("  •  ★ MY GUY" if recommendation.is_my_guy else "")
        )
        self.position_badge.setText(position)
        self.position_badge.setStyleSheet(
            "background-color: "
            f"{POSITION_COLORS.get(position, '#64748b')}; "
            "color: #071018; border-radius: 10px; "
            "font-weight: 900; padding: 7px 10px;"
        )

        self.score_label.setText(f"{recommendation.score:.0f}/100")
        self.grade_label.setText(recommendation.grade)
        self.grade_label.setStyleSheet(
            f"color: {self._grade_color(recommendation.grade)};"
        )
        self.survival_label.setText(survival_text)
        self.confidence_label.setText(
            f"CONFIDENCE {recommendation.confidence}%"
        )
        self.confidence_bar.setValue(recommendation.confidence)

        self.action_label.setText(recommendation.action)
        self.action_label.setProperty(
            "action", self._action_property(recommendation.action)
        )
        self.action_label.style().unpolish(self.action_label)
        self.action_label.style().polish(self.action_label)

        if survival is None:
            wait_text = "Usually gone before this pick"
        elif survival < 0.25:
            wait_text = f"High risk — only {survival:.1%} survives"
        elif survival < 0.60:
            wait_text = f"Meaningful risk — {survival:.1%} survives"
        else:
            wait_text = f"Lower risk — {survival:.1%} survives"

        tier_drop = recommendation.tier_drop_points
        if recommendation.tier_number <= 0:
            tier_text = "Tier data unavailable"
        else:
            tier_status = (
                f"Tier {recommendation.tier_number} — LAST PLAYER"
                if recommendation.is_last_in_tier
                else (
                    f"Tier {recommendation.tier_number} — "
                    f"{recommendation.players_remaining_in_tier} remain"
                )
            )
            drop_text = (
                f"next tier is {tier_drop:.1f} pts lower"
                if tier_drop > 0.0
                else "no measured next-tier cliff"
            )
            tier_text = (
                f"{tier_status}\n"
                f"{recommendation.tier_urgency} urgency · {drop_text}"
            )

        opportunity_cost = recommendation.opportunity_cost
        tier_risk = recommendation.tier_disappearance_probability

        if opportunity_cost >= 3.0:
            cost_headline = (
                f"TAKE-NOW PATH: +{opportunity_cost:.1f} PROJECTED POINTS"
            )
            headline_state = "take"
        elif opportunity_cost <= -3.0:
            cost_headline = (
                f"PASS PATH: +{abs(opportunity_cost):.1f} PROJECTED POINTS"
            )
            headline_state = "pass"
        else:
            cost_headline = "ROSTER PATHS PROJECT NEARLY EQUAL"
            headline_state = "neutral"

        self.cost_headline_label.setText(cost_headline)
        self.cost_headline_label.setProperty("state", headline_state)
        self.cost_headline_label.style().unpolish(self.cost_headline_label)
        self.cost_headline_label.style().polish(self.cost_headline_label)

        take_next = (
            recommendation.likely_take_next_player or "Best available"
        )
        pass_current = (
            recommendation.likely_pass_current_player or "Best available"
        )
        pass_next = (
            recommendation.likely_pass_next_player or "Best available"
        )

        self.take_path_frame.first_player_label.setText(
            recommendation.player_name
        )
        self.take_path_frame.second_player_label.setText(take_next)
        self.pass_path_frame.first_player_label.setText(pass_current)
        self.pass_path_frame.second_player_label.setText(pass_next)
        self.tier_risk_label.setText(
            f"TIER DISAPPEARANCE RISK  {tier_risk:.0%}"
        )

        self.wait_risk_card.value_label.setText(wait_text)
        self.roster_fit_card.value_label.setText(
            f"{recommendation.roster_need}  "
            f"{recommendation.roster_fit_score:+.1f}"
        )
        self.tier_drop_card.value_label.setText(tier_text)

        self.strategy_name_label.setText(recommendation.primary_strategy)
        self.strategy_confidence_label.setText(
            f"{recommendation.strategy_confidence}% confidence"
        )
        self.strategy_secondary_label.setText(
            f"Secondary: {recommendation.secondary_strategy or '—'}"
        )
        priorities = "  •  ".join(recommendation.strategy_priorities[:3])
        self.strategy_priority_label.setText(
            f"Next: {priorities or 'Best Value'}"
        )

        for name, value, maximum in (
            recommendation.score_breakdown.component_items()
        ):
            progress_bar, value_label = self.breakdown_rows[name]
            percentage = (value / maximum * 100.0) if maximum else 0.0
            progress_bar.setValue(round(percentage))
            value_label.setText(f"{value:.1f} / {maximum:.0f}")

        self.reason_label.setText(
            "\n".join(
                f"• {reason}"
                for reason in recommendation.reasons
            )
        )

        top_reasons = tuple(recommendation.reasons[:3])
        reason_text = (
            "\n".join(f"• {reason}" for reason in top_reasons)
            if top_reasons
            else "This player has the strongest overall recommendation profile."
        )
        self._set_live_insight(
            f"{recommendation.action}: {recommendation.player_name}",
            reason_text,
        )

    @staticmethod
    def _grade_color(grade: str) -> str:
        if grade in {"A+", "A"}:
            return "#4ade80"
        if grade in {"B+", "B"}:
            return "#facc15"
        if grade in {"C+", "C"}:
            return "#fb923c"
        return "#fb7185"

    @staticmethod
    def _action_property(action: str) -> str:
        if action == "DRAFT NOW":
            return "draft"
        if action == "RISKY TO WAIT":
            return "risk"
        if action == "CAN PROBABLY WAIT":
            return "wait"
        if action == "SAFE TO WAIT":
            return "safe"
        return "neutral"

    @staticmethod
    def _apply_table_color(
        item: QTableWidgetItem,
        column: int,
        grade: str,
        action: str,
        position: str,
    ) -> None:
        if column == 2:
            item.setForeground(
                QColor(
                    POSITION_COLORS.get(
                        position.upper(),
                        "#cbd5e1",
                    )
                )
            )
        elif column == 4:
            item.setForeground(
                QColor(
                    CommandCenterWidget._grade_color(
                        grade
                    )
                )
            )
        elif column == 6:
            item.setForeground(QColor("#fda4af"))
        elif column == 7:
            action_colors = {
                "DRAFT NOW": "#4ade80",
                "RISKY TO WAIT": "#fb923c",
                "CAN PROBABLY WAIT": "#facc15",
                "SAFE TO WAIT": "#93c5fd",
            }
            item.setForeground(
                QColor(
                    action_colors.get(
                        action,
                        "#cbd5e1",
                    )
                )
            )
