from __future__ import annotations

from PySide6.QtCore import QEvent, QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from asset_manager import DEFAULT_ASSET_MANAGER, short_player_name
from preferences import normalize_name
from team import base_position


POSITION_FALLBACK_COLORS = {
    "QB": "#7c3aed",
    "RB": "#047857",
    "WR": "#0369a1",
    "TE": "#c2410c",
    "DST": "#475569",
    "K": "#a16207",
}


class DraftPickCard(QFrame):
    """One draft-board pick card with local assets and hover intelligence."""

    _team_logo_cache: dict[tuple[str, int, int, int], QPixmap] = {}

    hovered = Signal(object)
    hover_ended = Signal()

    def __init__(
        self,
        *,
        overall_pick: int,
        round_number: int,
        pick_in_round: int,
        team_number: int,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.overall_pick = overall_pick
        self.round_number = round_number
        self.pick_in_round = pick_in_round
        self.team_number = team_number

        self._draft_pick = None
        self._projection = None
        self._is_my_guy = False
        self._is_current = False
        self._pulse_on = False
        self._hover_shadow: QGraphicsDropShadowEffect | None = None

        self.setObjectName("DraftPickCard")
        self.setProperty("position", "empty")
        self.setProperty("userTeam", "false")
        self.setProperty("currentPick", "false")
        self.setProperty("pulse", "false")
        self.setProperty("hovered", "false")
        self.setMinimumSize(148, 82)
        self.setMaximumHeight(96)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(650)
        self._pulse_timer.timeout.connect(self._toggle_pulse)

        self._build_ui()
        self.show_empty()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 8, 7)
        layout.setSpacing(3)

        # Pick number always remains visible and is enough context for an empty slot.
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        self.pick_label = QLabel()
        self.pick_label.setObjectName("DraftCardPick")
        top_row.addWidget(self.pick_label)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        # Current-pick indicator gets its own centered row instead of competing with
        # the pick number or future AI badges.
        self.clock_badge = QLabel("ON CLOCK")
        self.clock_badge.setObjectName("DraftCardClockBadge")
        self.clock_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_badge.setFixedWidth(74)
        self.clock_badge.hide()
        layout.addWidget(self.clock_badge, 0, Qt.AlignmentFlag.AlignHCenter)

        self.content_widget = QFrame()
        self.content_widget.setObjectName("DraftCardContent")
        content_row = QHBoxLayout(self.content_widget)
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(5)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.player_label = QLabel()
        self.player_label.setObjectName("DraftCardPlayer")
        self.player_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        self.player_label.setWordWrap(False)
        text_layout.addWidget(self.player_label)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(5)

        self.position_label = QLabel()
        self.position_label.setObjectName("DraftCardPosition")
        meta_row.addWidget(self.position_label)

        self.team_logo_label = QLabel()
        self.team_logo_label.setObjectName("DraftCardTeamLogo")
        self.team_logo_label.setFixedSize(20, 20)
        self.team_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.team_logo_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        # Explicitly override the application-wide QWidget background. The downloaded
        # logo PNGs already contain alpha; the black boxes were the QLabel background.
        self.team_logo_label.setStyleSheet(
            "QLabel#DraftCardTeamLogo { background: transparent; border: 0; }"
        )
        meta_row.addWidget(self.team_logo_label)

        self.team_label = QLabel()
        self.team_label.setObjectName("DraftCardTeam")
        meta_row.addWidget(self.team_label)
        meta_row.addStretch(1)

        text_layout.addLayout(meta_row)
        content_row.addLayout(text_layout, 1)

        self.headshot_label = QLabel()
        self.headshot_label.setObjectName("DraftCardHeadshot")
        self.headshot_label.setFixedSize(52, 52)
        self.headshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.headshot_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        content_row.addWidget(
            self.headshot_label,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        layout.addWidget(self.content_widget, 1)

    def show_empty(self) -> None:
        self._draft_pick = None
        self._projection = None
        self._is_my_guy = False

        self.pick_label.setText(f"{self.round_number}.{self.pick_in_round:02d}")
        self.player_label.clear()
        self.position_label.clear()
        self.team_label.clear()
        self.team_logo_label.clear()
        self.headshot_label.clear()

        # Truly empty means truly empty: no avatar/logo placeholder rectangles.
        self.team_logo_label.hide()
        self.headshot_label.hide()
        self.content_widget.hide()

        self.setProperty("position", "empty")
        self._refresh_style()

    def show_player(
        self,
        draft_pick,
        approved_players: set[str],
        projection=None,
    ) -> None:
        self._draft_pick = draft_pick
        self._projection = projection

        player = draft_pick.player
        position = base_position(player.position)
        self._is_my_guy = normalize_name(player.name) in approved_players

        self.pick_label.setText(f"{self.round_number}.{self.pick_in_round:02d}")
        self.player_label.setText(short_player_name(player.name))
        self.position_label.setText(player.position)
        self.team_label.setText(player.team)
        self.setProperty("position", position.lower())

        self.content_widget.show()
        self.headshot_label.show()
        self._set_team_logo(player.team)
        self._set_headshot(player.name, position)
        self._refresh_style()

    def _set_team_logo(self, team: str) -> None:
        """Render a crisp logo on Retina/HiDPI displays.

        Qt widgets use logical pixels while a Retina screen can need two physical
        pixels for every logical pixel.  Scaling directly to 20x20 therefore looks
        soft on macOS.  We scale to the device-pixel size, mark the pixmap with the
        correct DPR, and cache the result for reuse.
        """
        path = DEFAULT_ASSET_MANAGER.team_logo(team)
        if path is None:
            self.team_logo_label.clear()
            self.team_logo_label.hide()
            return

        dpr = max(1.0, float(self.devicePixelRatioF()))
        logical = self.team_logo_label.size()
        pixel_width = max(1, round(logical.width() * dpr))
        pixel_height = max(1, round(logical.height() * dpr))
        cache_key = (
            str(path),
            pixel_width,
            pixel_height,
            round(dpr * 100),
        )

        cached = self._team_logo_cache.get(cache_key)
        if cached is not None and not cached.isNull():
            self.team_logo_label.setPixmap(cached)
            self.team_logo_label.show()
            return

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.team_logo_label.clear()
            self.team_logo_label.hide()
            return

        scaled = pixmap.scaled(
            QSize(pixel_width, pixel_height),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(dpr)
        self._team_logo_cache[cache_key] = scaled
        self.team_logo_label.setPixmap(scaled)
        self.team_logo_label.show()

    def _set_headshot(self, player_name: str, position: str) -> None:
        path = DEFAULT_ASSET_MANAGER.headshot(player_name)
        if path is not None:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.headshot_label.setPixmap(self._rounded_pixmap(pixmap))
                self.headshot_label.setText("")
                self.headshot_label.show()
                return

        self.headshot_label.setPixmap(QPixmap())
        self.headshot_label.setText(self._initials(player_name))
        fallback = POSITION_FALLBACK_COLORS.get(position, "#475569")
        self.headshot_label.setStyleSheet(
            "QLabel#DraftCardHeadshot {"
            f"background-color: {fallback};"
            "border: 1px solid rgba(255,255,255,0.18);"
            "border-radius: 12px;"
            "color: #f8fafc;"
            "font-size: 14px;"
            "font-weight: 900;"
            "}"
        )
        self.headshot_label.show()

    def _rounded_pixmap(self, pixmap: QPixmap) -> QPixmap:
        size = self.headshot_label.size()
        scaled = pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        cropped = scaled.copy(x, y, size.width(), size.height())

        result = QPixmap(size)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(result.rect()), 12, 12)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, cropped)
        painter.end()

        self.headshot_label.setStyleSheet(
            "QLabel#DraftCardHeadshot { background: transparent; border: 0; }"
        )
        return result

    @staticmethod
    def _initials(name: str) -> str:
        parts = [part for part in name.replace("-", " ").split() if part]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def hover_payload(self) -> dict[str, object] | None:
        if self._draft_pick is None:
            return None

        player = self._draft_pick.player
        return {
            "name": player.name,
            "position": player.position,
            "team": player.team,
            "rank": getattr(player, "rank", None),
            "tier": getattr(player, "tier", None),
            "bye": getattr(player, "bye", None),
            "projected_points": getattr(self._projection, "fantasy_points", None),
            "is_my_guy": self._is_my_guy,
            "round_number": self.round_number,
            "pick_in_round": self.pick_in_round,
        }

    def set_user_team(self, enabled: bool) -> None:
        self.setProperty("userTeam", "true" if enabled else "false")
        self._refresh_style()

    def set_current_pick(self, enabled: bool) -> None:
        self._is_current = enabled
        self.setProperty("currentPick", "true" if enabled else "false")

        if enabled:
            self.clock_badge.show()
            self._pulse_on = True
            self.setProperty("pulse", "true")
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self.clock_badge.hide()
            self._pulse_on = False
            self.setProperty("pulse", "false")

        self._refresh_style()

    def _toggle_pulse(self) -> None:
        if not self._is_current:
            return
        self._pulse_on = not self._pulse_on
        self.setProperty("pulse", "true" if self._pulse_on else "false")
        self._refresh_style()

    def _enable_hover_shadow(self) -> None:
        if self._draft_pick is None:
            return
        if self._hover_shadow is None:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(18)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 150))
            self._hover_shadow = shadow
            self.setGraphicsEffect(self._hover_shadow)
        self._hover_shadow.setEnabled(True)

    def _disable_hover_shadow(self) -> None:
        if self._hover_shadow is not None:
            self._hover_shadow.setEnabled(False)

    def _refresh_style(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def enterEvent(self, event: QEvent) -> None:
        self.setProperty("hovered", "true")
        self._enable_hover_shadow()
        self._refresh_style()
        payload = self.hover_payload()
        if payload is not None:
            self.hovered.emit(payload)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setProperty("hovered", "false")
        self._disable_hover_shadow()
        self._refresh_style()
        if self._draft_pick is not None:
            self.hover_ended.emit()
        super().leaveEvent(event)
