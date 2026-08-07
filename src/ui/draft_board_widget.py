from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from live_draft import LiveDraftSession
from preferences import normalize_name
from projection_loader import load_projections
from ui.draft_pick_card import DraftPickCard


class DraftBoardWidget(QWidget):
    """Card-based live draft board with rich cards and fixed hover intelligence."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._cards: dict[int, DraftPickCard] = {}
        self._team_headers: dict[int, QFrame] = {}
        self._user_team_number: int | None = None
        self._projections = load_projections()

        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        self.header_card = QFrame()
        self.header_card.setObjectName("DraftRoomHeaderCard")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(18)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(2)

        title = QLabel("GRIDIRON AI • LIVE DRAFT ROOM")
        title.setObjectName("DraftRoomTitle")
        title_stack.addWidget(title)

        self.summary_label = QLabel("No active draft.")
        self.summary_label.setObjectName("DraftRoomSummary")
        title_stack.addWidget(self.summary_label)
        header_layout.addLayout(title_stack, 1)

        progress_stack = QVBoxLayout()
        progress_stack.setSpacing(4)
        progress_title = QLabel("DRAFT PROGRESS")
        progress_title.setObjectName("DraftRoomMetaTitle")
        progress_stack.addWidget(progress_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("DraftRoomProgress")
        self.progress_bar.setRange(0, 160)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setFixedHeight(10)
        progress_stack.addWidget(self.progress_bar)
        header_layout.addLayout(progress_stack)

        self.on_clock_label = QLabel("WAITING FOR DRAFT")
        self.on_clock_label.setObjectName("DraftRoomOnClock")
        self.on_clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.on_clock_label.setMinimumWidth(185)
        header_layout.addWidget(self.on_clock_label)
        outer.addWidget(self.header_card)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("DraftBoardScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.board_content = QWidget()
        self.board_content.setObjectName("DraftBoardCanvas")
        self.grid = QGridLayout(self.board_content)
        self.grid.setContentsMargins(8, 8, 8, 12)
        self.grid.setHorizontalSpacing(7)
        self.grid.setVerticalSpacing(7)

        self._build_team_headers()
        self._build_round_rows()

        self.scroll_area.setWidget(self.board_content)
        outer.addWidget(self.scroll_area, 1)

        self.footer_card = QFrame()
        self.footer_card.setObjectName("DraftRoomFooter")
        footer_layout = QHBoxLayout(self.footer_card)
        footer_layout.setContentsMargins(12, 7, 12, 7)
        footer_layout.setSpacing(14)

        legend = QWidget()
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(12)
        legend_layout.addWidget(self._legend_item("●", "RB", "#34d399"))
        legend_layout.addWidget(self._legend_item("●", "WR", "#38bdf8"))
        legend_layout.addWidget(self._legend_item("●", "QB", "#a855f7"))
        legend_layout.addWidget(self._legend_item("●", "TE", "#fb923c"))
        legend_layout.addWidget(self._legend_item("★", "My Guy", "#facc15"))
        footer_layout.addWidget(legend)

        divider = QFrame()
        divider.setObjectName("DraftRoomFooterDivider")
        divider.setFrameShape(QFrame.Shape.VLine)
        footer_layout.addWidget(divider)

        self.hover_intel_label = QLabel(
            "Hover a drafted player for rank, tier, projection, bye week, and pick context."
        )
        self.hover_intel_label.setObjectName("DraftRoomHoverIntel")
        self.hover_intel_label.setWordWrap(False)
        footer_layout.addWidget(self.hover_intel_label, 1)

        self.footer_hint = QLabel("Your column is highlighted • Current pick pulses")
        self.footer_hint.setObjectName("DraftRoomLegendText")
        footer_layout.addWidget(self.footer_hint)

        outer.addWidget(self.footer_card)

    def _build_team_headers(self) -> None:
        spacer = QLabel("ROUND")
        spacer.setObjectName("DraftRoundHeader")
        spacer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spacer.setFixedWidth(58)
        self.grid.addWidget(spacer, 0, 0)

        for team_number in range(1, 11):
            frame = QFrame()
            frame.setObjectName("DraftTeamHeader")
            frame.setProperty("userTeam", "false")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(8, 9, 8, 9)
            layout.setSpacing(0)

            name = QLabel(f"TEAM {team_number}")
            name.setObjectName("DraftTeamName")
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(name)

            frame.setMinimumWidth(148)
            self.grid.addWidget(frame, 0, team_number)
            self._team_headers[team_number] = frame

    def _build_round_rows(self) -> None:
        overall = 1

        for round_number in range(1, 17):
            round_label = QLabel(f"R{round_number}")
            round_label.setObjectName("DraftRoundLabel")
            round_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            round_label.setFixedWidth(58)
            round_label.setMinimumHeight(82)
            self.grid.addWidget(round_label, round_number, 0)

            team_order = (
                range(1, 11)
                if round_number % 2 == 1
                else range(10, 0, -1)
            )

            for pick_in_round, team_number in enumerate(team_order, start=1):
                card = DraftPickCard(
                    overall_pick=overall,
                    round_number=round_number,
                    pick_in_round=pick_in_round,
                    team_number=team_number,
                )
                card.hovered.connect(self._show_hover_intel)
                card.hover_ended.connect(self._reset_hover_intel)
                self.grid.addWidget(card, round_number, team_number)
                self._cards[overall] = card
                overall += 1

        for column in range(1, 11):
            self.grid.setColumnStretch(column, 1)

    def _legend_item(self, symbol: str, text: str, color: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet(
            f"background: transparent; border: 0; color: {color}; font-weight: 900;"
        )
        layout.addWidget(symbol_label)

        text_label = QLabel(text)
        text_label.setObjectName("DraftRoomLegendText")
        layout.addWidget(text_label)
        return widget

    def refresh_board(
        self,
        session: LiveDraftSession | None,
        approved_players: set[str],
    ) -> None:
        for card in self._cards.values():
            card.show_empty()
            card.set_current_pick(False)
            card.set_user_team(False)

        for header in self._team_headers.values():
            header.setProperty("userTeam", "false")
            self._refresh_widget(header)

        self._user_team_number = None
        self._reset_hover_intel()

        if session is None:
            self.summary_label.setText("No active draft.")
            self.progress_bar.setValue(0)
            self.on_clock_label.setText("WAITING FOR DRAFT")
            self.on_clock_label.setProperty("userTurn", "false")
            self._refresh_widget(self.on_clock_label)
            return

        self._user_team_number = session.user_team_number
        completed = len(session.draft_results)

        self.summary_label.setText(
            f"10-team • 16 rounds • {completed}/160 picks complete • "
            f"Your slot: {session.user_team_number}"
        )
        self.progress_bar.setValue(completed)

        current_team = session.current_team_number
        if current_team is None:
            self.on_clock_label.setText("DRAFT COMPLETE")
            self.on_clock_label.setProperty("userTurn", "false")
        elif current_team == session.user_team_number:
            self.on_clock_label.setText(f"● YOU'RE ON THE CLOCK • PICK {session.current_pick}")
            self.on_clock_label.setProperty("userTurn", "true")
        else:
            self.on_clock_label.setText(f"TEAM {current_team} ON CLOCK • PICK {session.current_pick}")
            self.on_clock_label.setProperty("userTurn", "false")
        self._refresh_widget(self.on_clock_label)

        for team_number, header in self._team_headers.items():
            is_user = team_number == session.user_team_number
            header.setProperty("userTeam", "true" if is_user else "false")
            self._refresh_widget(header)

            name = header.findChild(QLabel, "DraftTeamName")
            if name is not None:
                name.setText("YOU" if is_user else f"TEAM {team_number}")

        picks_by_overall = {
            draft_pick.overall: draft_pick
            for draft_pick in session.draft_results
        }

        for overall_pick, team_number in enumerate(
            session.league.draft_order,
            start=1,
        ):
            card = self._cards[overall_pick]
            card.set_user_team(team_number == session.user_team_number)

            draft_pick = picks_by_overall.get(overall_pick)
            if draft_pick is not None:
                projection = self._projections.get(
                    normalize_name(draft_pick.player.name)
                )
                card.show_player(
                    draft_pick,
                    approved_players,
                    projection=projection,
                )

            if overall_pick == session.current_pick and not session.is_complete:
                card.set_current_pick(True)

        self._scroll_to_current_pick(session.current_pick)

    def _show_hover_intel(self, payload: dict[str, object]) -> None:
        name = payload.get("name") or "Player"
        position = payload.get("position") or "—"
        team = payload.get("team") or "—"
        rank = payload.get("rank")
        tier = payload.get("tier")
        bye = payload.get("bye")
        projected_points = payload.get("projected_points")
        round_number = payload.get("round_number")
        pick_in_round = payload.get("pick_in_round")
        is_my_guy = bool(payload.get("is_my_guy"))

        parts = [f"{name}  •  {position} {team}"]
        if isinstance(rank, int):
            parts.append(f"Rank {rank}")
        if isinstance(tier, int) and tier > 0:
            parts.append(f"Tier {tier}")
        if isinstance(projected_points, (int, float)):
            parts.append(f"{projected_points:.1f} projected pts")
        if isinstance(bye, int) and bye > 0:
            parts.append(f"Bye {bye}")
        if isinstance(round_number, int) and isinstance(pick_in_round, int):
            parts.append(f"Pick {round_number}.{pick_in_round:02d}")
        if is_my_guy:
            parts.append("★ My Guy")

        self.hover_intel_label.setText("   •   ".join(parts))
        self.hover_intel_label.setProperty("active", "true")
        self._refresh_widget(self.hover_intel_label)

    def _reset_hover_intel(self) -> None:
        self.hover_intel_label.setText(
            "Hover a drafted player for rank, tier, projection, bye week, and pick context."
        )
        self.hover_intel_label.setProperty("active", "false")
        self._refresh_widget(self.hover_intel_label)

    def _scroll_to_current_pick(self, current_pick: int) -> None:
        card = self._cards.get(current_pick)
        if card is None:
            return
        self.scroll_area.ensureWidgetVisible(card, 80, 80)

    @staticmethod
    def _refresh_widget(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
