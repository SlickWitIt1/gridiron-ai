from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from project_paths import ASSETS_DIR, PLAYER_ASSETS_FILE, TEAM_LOGOS_DIR


_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalized_asset_name(name: str) -> str:
    """Create a stable player key for asset lookup and filenames."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.casefold().replace("’", "'")
    return "".join(character for character in text if character.isalnum())


def asset_filename(name: str) -> str:
    """Create a readable, filesystem-safe filename stem."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.casefold().replace("’", "'")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "player"


def short_player_name(name: str) -> str:
    """Sleeper-style compact display name while preserving meaningful surnames/suffixes."""
    parts = [part for part in name.strip().split() if part]
    if len(parts) <= 1:
        return name.strip()

    first = parts[0]
    last_parts = parts[1:]

    # Preserve suffixes and multi-token surnames such as St. Brown, Van Jefferson,
    # Dell'Orso, etc. We intentionally keep everything after the first name.
    initial = next((character for character in first if character.isalpha()), first[:1])
    if not initial:
        return name.strip()

    return f"{initial.upper()}. {' '.join(last_parts)}"


class AssetManager:
    """Resolve local visual assets without coupling them to the Player model."""

    def __init__(self, manifest_path: str | Path = PLAYER_ASSETS_FILE) -> None:
        self.manifest_path = Path(manifest_path)
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, dict[str, object]]:
        if not self.manifest_path.is_file():
            return {}

        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

        if isinstance(payload, dict) and "players" in payload:
            players = payload.get("players")
            return players if isinstance(players, dict) else {}

        return payload if isinstance(payload, dict) else {}

    def reload(self) -> None:
        self._manifest = self._load_manifest()
        self.headshot.cache_clear()
        self.team_logo.cache_clear()

    def entry(self, player_name: str) -> dict[str, object] | None:
        value = self._manifest.get(normalized_asset_name(player_name))
        return value if isinstance(value, dict) else None

    @lru_cache(maxsize=1024)
    def headshot(self, player_name: str) -> Path | None:
        entry = self.entry(player_name)
        if not entry:
            return None

        relative = entry.get("headshot")
        if not isinstance(relative, str) or not relative:
            return None

        path = ASSETS_DIR / relative
        return path if path.is_file() else None

    @lru_cache(maxsize=64)
    def team_logo(self, team: str) -> Path | None:
        normalized_team = team.strip().upper()
        if not normalized_team:
            return None

        for extension in ("png", "webp", "jpg", "jpeg"):
            path = TEAM_LOGOS_DIR / f"{normalized_team}.{extension}"
            if path.is_file():
                return path
        return None


DEFAULT_ASSET_MANAGER = AssetManager()
