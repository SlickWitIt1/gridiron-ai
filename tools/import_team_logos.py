#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import ssl
import sys
from collections import deque
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from loader import load_players
from project_paths import TEAM_LOGOS_DIR, ensure_asset_directories


USER_AGENT = "GridironAI-TeamLogoImporter/1.2"
# Keep a large transparent master on disk. The UI downsamples from this
# high-resolution source for sharp Retina/HiDPI rendering.
LOGO_SIZE = (256, 256)

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


def _color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    return max(abs(left[index] - right[index]) for index in range(3))


def remove_uniform_edge_background(image, tolerance: int = 10):
    """Remove only a flat opaque background connected to the outside edge.

    This is intentionally conservative. Black that belongs to a Raiders/Falcons/etc.
    logo remains untouched unless it is part of the flat canvas background connected
    to an image edge.
    """
    from PIL import Image

    rgba = image.convert("RGBA")
    width, height = rgba.size
    if width < 2 or height < 2:
        return rgba

    pixels = rgba.load()
    corners = (
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    )

    opaque_corners = [corner for corner in corners if corner[3] >= 245]
    if len(opaque_corners) < 3:
        return rgba

    reference = opaque_corners[0][:3]
    similar_corners = sum(
        1
        for corner in opaque_corners
        if _color_distance(corner[:3], reference) <= tolerance
    )
    if similar_corners < 3:
        return rgba

    # Do not erase light/white backgrounds automatically; those can be legitimate
    # white logo details touching the edge in source art. The issue we are cleaning
    # is the dark opaque canvas occasionally returned by image sources.
    if max(reference) > 60:
        return rgba

    queue: deque[tuple[int, int]] = deque()
    visited: set[tuple[int, int]] = set()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))

        red, green, blue, alpha = pixels[x, y]
        if alpha < 245 or _color_distance((red, green, blue), reference) > tolerance:
            continue

        pixels[x, y] = (red, green, blue, 0)

        if x > 0:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    return rgba


def normalize_logo(image, size: tuple[int, int] = LOGO_SIZE):
    from PIL import Image

    cleaned = remove_uniform_edge_background(image)
    cleaned.thumbnail(size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    x = (size[0] - cleaned.width) // 2
    y = (size[1] - cleaned.height) // 2
    canvas.alpha_composite(cleaned, (x, y))
    return canvas


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
        normalize_logo(image).save(destination, format="PNG", optimize=True)


def clean_cached_logo(path: Path) -> None:
    """Normalize an already-downloaded logo in place without re-downloading it."""
    from PIL import Image

    with Image.open(path) as image:
        normalized = normalize_logo(image)
    normalized.save(path, format="PNG", optimize=True)


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
    codes.update(NFL_TEAM_CODES)
    return tuple(sorted(codes))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and normalize high-resolution NFL team logos."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Re-download every logo from the high-resolution source. "
            "Use this once after upgrading from the old 96px cache."
        ),
    )
    args = parser.parse_args()

    ensure_asset_directories()
    team_codes = team_codes_from_rankings()

    downloaded = 0
    cached = 0
    cleaned = 0
    failures: list[tuple[str, str]] = []

    print("Importing high-resolution NFL team logos...")

    for index, team_code in enumerate(team_codes, start=1):
        destination = TEAM_LOGOS_DIR / f"{team_code}.png"

        if (
            destination.is_file()
            and destination.stat().st_size > 0
            and not args.force
        ):
            try:
                clean_cached_logo(destination)
                cleaned += 1
                cached += 1
                print(f"[{index:>2}/{len(team_codes)}] CLEAN   {team_code}")
            except (OSError, ValueError) as error:
                failures.append((team_code, str(error)))
                print(f"[{index:>2}/{len(team_codes)}] FAILED  {team_code}")
            continue

        try:
            raw = fetch_bytes(logo_url(team_code))
            save_logo(raw, destination)
            downloaded += 1
            state = "REFRESH" if args.force else "OK"
            print(f"[{index:>2}/{len(team_codes)}] {state:<7} {team_code}")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            failures.append((team_code, str(error)))
            print(f"[{index:>2}/{len(team_codes)}] FAILED  {team_code}")

    print("\n====================================")
    print(" GRIDIRON AI RETINA LOGO IMPORT")
    print("====================================")
    print(f"Teams processed: {len(team_codes)}")
    print(f"Downloaded:      {downloaded}")
    print(f"Cached:          {cached}")
    print(f"Normalized:      {cleaned + downloaded}")
    print(f"Master size:     {LOGO_SIZE[0]}x{LOGO_SIZE[1]}")
    print(f"Failures:        {len(failures)}")
    print(f"Logo directory:  {TEAM_LOGOS_DIR}")

    if failures:
        print("\nFAILURES")
        for team_code, message in failures:
            print(f"- {team_code}: {message}")


if __name__ == "__main__":
    main()
