from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class WarRoomHeader(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self.reset()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        brand = QFrame()
        brand.setObjectName("BrandCard")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(18, 10, 18, 10)
        brand_layout.setSpacing(0)

        title = QLabel("GRIDIRON AI")
        title.setObjectName("WarRoomTitle")
        subtitle = QLabel("LIVE DRAFT WAR ROOM  •  v0.7 ALPHA")
        subtitle.setObjectName("WarRoomSubtitle")
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand, 2)

        self.on_clock_card = QFrame()
        self.on_clock_card.setObjectName("OnClockCard")
        clock_layout = QVBoxLayout(self.on_clock_card)
        clock_layout.setContentsMargins(16, 9, 16, 9)
        clock_layout.setSpacing(1)

        self.turn_label = QLabel("NO ACTIVE DRAFT")
        self.turn_label.setObjectName("OnClockTitle")
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pick_label = QLabel("Start or resume a draft")
        self.pick_label.setObjectName("OnClockMeta")
        self.pick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.turn_label)
        clock_layout.addWidget(self.pick_label)
        layout.addWidget(self.on_clock_card, 2)

        progress = QFrame()
        progress.setObjectName("DraftProgressCard")
        progress_layout = QVBoxLayout(progress)
        progress_layout.setContentsMargins(16, 9, 16, 9)
        progress_layout.setSpacing(4)

        self.next_pick_label = QLabel("NEXT PICK  —")
        self.next_pick_label.setObjectName("DraftProgressTitle")
        self.draft_progress = QProgressBar()
        self.draft_progress.setRange(0, 160)
        self.draft_progress.setTextVisible(False)
        self.draft_progress.setObjectName("DraftProgressBar")
        self.progress_meta_label = QLabel("0 of 160 picks complete")
        self.progress_meta_label.setObjectName("DraftProgressMeta")
        progress_layout.addWidget(self.next_pick_label)
        progress_layout.addWidget(self.draft_progress)
        progress_layout.addWidget(self.progress_meta_label)
        layout.addWidget(progress, 2)

    def reset(self) -> None:
        self.turn_label.setText("NO ACTIVE DRAFT")
        self.pick_label.setText("Start or resume a draft")
        self.next_pick_label.setText("NEXT PICK  —")
        self.draft_progress.setValue(0)
        self.progress_meta_label.setText("0 of 160 picks complete")
        self.on_clock_card.setProperty("userTurn", False)
        self._repolish(self.on_clock_card)

    def update_state(self, session) -> None:
        if session is None:
            self.reset()
            return

        completed = len(session.draft_results)
        self.draft_progress.setMaximum(len(session.league.draft_order))
        self.draft_progress.setValue(completed)
        self.progress_meta_label.setText(
            f"{completed} of {len(session.league.draft_order)} picks complete"
        )

        if session.is_complete:
            self.turn_label.setText("DRAFT COMPLETE")
            self.pick_label.setText("All roster spots have been selected")
            self.next_pick_label.setText("NEXT PICK  —")
            self.on_clock_card.setProperty("userTurn", False)
            self._repolish(self.on_clock_card)
            return

        current_pick = session.current_pick
        current_round = ((current_pick - 1) // session.league.num_teams) + 1
        pick_in_round = ((current_pick - 1) % session.league.num_teams) + 1

        if session.is_user_turn:
            self.turn_label.setText("●  YOU'RE ON THE CLOCK")
            self.on_clock_card.setProperty("userTurn", True)
        else:
            self.turn_label.setText(f"TEAM {session.current_team_number} ON CLOCK")
            self.on_clock_card.setProperty("userTurn", False)

        self.pick_label.setText(
            f"ROUND {current_round}  •  PICK {pick_in_round}  •  OVERALL {current_pick}"
        )

        next_pick = session.next_user_pick
        if session.is_user_turn:
            next_text = f"NEXT TURN  PICK {next_pick}" if next_pick else "FINAL PICK"
        elif next_pick is not None:
            picks_away = max(0, next_pick - current_pick)
            next_text = f"YOUR PICK  {next_pick}  •  {picks_away} PICKS AWAY"
        else:
            next_text = "NO PICKS REMAINING"
        self.next_pick_label.setText(next_text)
        self._repolish(self.on_clock_card)

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
