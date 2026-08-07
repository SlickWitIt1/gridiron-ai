from dataclasses import dataclass
from enum import Enum


class CoachMessageType(Enum):
    RECOMMENDATION = "Recommendation"
    FOLLOWED = "Recommendation Followed"
    DEVIATION = "Recommendation Changed"
    UPDATE = "Draft Update"


class CoachSeverity(Enum):
    INFO = "Info"
    POSITIVE = "Positive"
    WARNING = "Warning"


@dataclass(frozen=True, slots=True)
class CoachMessage:
    """Structured copy produced by the adaptive draft coach."""

    message_type: CoachMessageType
    severity: CoachSeverity
    title: str
    summary: str
    bullets: tuple[str, ...] = ()
    action: str | None = None
    recommended_player: str | None = None
    selected_player: str | None = None

    @property
    def body_lines(self) -> tuple[str, ...]:
        """Return display-ready lines without forcing a UI implementation."""
        lines = [self.summary]
        lines.extend(f"• {bullet}" for bullet in self.bullets)
        if self.action:
            lines.append(self.action)
        return tuple(lines)
