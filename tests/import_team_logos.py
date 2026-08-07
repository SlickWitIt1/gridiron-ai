#!/usr/bin/env python3
from __future__ import annotations

import io
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from loader import load_players
from project_paths import TEAM_LOGOS_DIR, ensure_asset_directories


USER_AGENT = "GridironAI-TeamLogoImporter/1.0"
LOGO_SIZE = (96, 96)

# FantasyPros / Gridiron team codes. JAC and WAS are deliberately kept because
# those are common fantasy-data abbreviations even though ESPN uses JAX / WSH.
NFL_TEAM_CODES = (
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAC", "KC",
    "LV", "LAC", "LAR", "MIA", "MIN", "NE", "NO", "NYG",
    "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
)

ESPN_CODE_OVERRIDES = {
    "JAC": "JAX",
    "WAS": "WSH",
}

IGNORED_TEAM_CODES = {"", "FA", "NONE", "N/A", "NA"}


def build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


SSL_CONTEXT = build_ssl_context()


def espn_code_for(team_code: str) -> str:
    normalized = team_code.strip().upper()
    return ESPN_CODE_OVERRIDES.get(normalized, normalized).lower()


def logo_url(team_code: str) -> str:
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{espn_code_for(team_code)}.png"


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/png,image/*,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return response.read()


def save_logo(image_bytes: bytes, destination: Path) -> None:
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError(
            "Pillow is required for the one-time team-logo importer. "
            "Install it with: python3 -m pip install Pillow"
        ) from error

    destination.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(io.BytesIO(image_bytes)) as image:
        image = image.convert("RGBA")
        image.thumbnail(LOGO_SIZE, Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", LOGO_SIZE, (0, 0, 0, 0))
        x = (LOGO_SIZE[0] - image.width) // 2
        y = (LOGO_SIZE[1] - image.height) // 2
        canvas.alpha_composite(image, (x, y))
        canvas.save(destination, format="PNG", optimize=True)


def team_codes_from_rankings() -> tuple[str, ...]:
    codes = {
        str(player.team or "").strip().upper()
        for player in load_players()
    }
    codes = {
        code
        for code in codes
        if code not in IGNORED_TEAM_CODES
    }

    # Always include the complete league so logos remain available even when a
    # particular team is temporarily absent from the current fantasy rankings.
    codes.update(NFL_TEAM_CODES)
    return tuple(sorted(codes))


def main() -> None:
    ensure_asset_directories()
    team_codes = team_codes_from_rankings()

    downloaded = 0
    cached = 0
    failures: list[tuple[str, str]] = []

    print("Importing NFL team logos...")

    for index, team_code in enumerate(team_codes, start=1):
        destination = TEAM_LOGOS_DIR / f"{team_code}.png"

        if destination.is_file() and destination.stat().st_size > 0:
            cached += 1
            print(f"[{index:>2}/{len(team_codes)}] CACHED  {team_code}")
            continue

        try:
            raw = fetch_bytes(logo_url(team_code))
            save_logo(raw, destination)
            downloaded += 1
            print(f"[{index:>2}/{len(team_codes)}] OK      {team_code}")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            failures.append((team_code, str(error)))
            print(f"[{index:>2}/{len(team_codes)}] FAILED  {team_code}")

    print("\n====================================")
    print(" GRIDIRON AI TEAM LOGO IMPORT")
    print("====================================")
    print(f"Teams processed: {len(team_codes)}")
    print(f"Downloaded:      {downloaded}")
    print(f"Already cached:  {cached}")
    print(f"Failures:        {len(failures)}")
    print(f"Logo directory:  {TEAM_LOGOS_DIR}")

    if failures:
        print("\nFAILURES")
        for team_code, message in failures:
            print(f"- {team_code}: {message}")


if __name__ == "__main__":
    main()
