#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import ssl
import sys
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from asset_manager import asset_filename, normalized_asset_name
from loader import load_players
from project_paths import (
    ASSETS_DIR,
    HEADSHOTS_DIR,
    PLAYER_ASSETS_FILE,
    SLEEPER_PLAYERS_CACHE_FILE,
    ensure_asset_directories,
)
from team import base_position


PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
HEADSHOT_URL = "https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
USER_AGENT = "GridironAI-AssetImporter/1.1"
IMAGE_SIZE = (256, 256)

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

# Only use aliases when the football identity is unambiguous.
# Most suffix/team discrepancies are handled by the matcher below.
PLAYER_NAME_ALIASES = {
    normalized_asset_name("Hollywood Brown"): "Marquise Brown",
    normalized_asset_name("Bam Knight"): "Zonovan Knight",
}


def build_ssl_context() -> ssl.SSLContext:
    """Use certifi automatically when available; otherwise use Python defaults."""
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()

    return ssl.create_default_context(cafile=certifi.where())


SSL_CONTEXT = build_ssl_context()


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,image/*,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return response.read()


def load_existing_manifest() -> dict[str, object]:
    if not PLAYER_ASSETS_FILE.is_file():
        return {
            "version": 1,
            "source": "Sleeper NFL player map + Sleeper CDN player images",
            "players": {},
        }

    try:
        payload = json.loads(PLAYER_ASSETS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "version": 1,
            "source": "Sleeper NFL player map + Sleeper CDN player images",
            "players": {},
        }

    if not isinstance(payload, dict):
        payload = {}

    players = payload.get("players")
    if not isinstance(players, dict):
        players = {}

    return {
        "version": 1,
        "source": "Sleeper NFL player map + Sleeper CDN player images",
        "players": players,
    }


def load_sleeper_players(refresh: bool) -> dict[str, dict[str, object]]:
    ensure_asset_directories()

    if SLEEPER_PLAYERS_CACHE_FILE.is_file() and not refresh:
        payload = json.loads(SLEEPER_PLAYERS_CACHE_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload

    print("Fetching Sleeper NFL player map...")
    raw = fetch_bytes(PLAYERS_URL, timeout=60)
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Sleeper player endpoint returned an unexpected payload.")

    SLEEPER_PLAYERS_CACHE_FILE.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return payload


def external_full_name(record: dict[str, object]) -> str:
    for key in ("full_name", "search_full_name"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    first = str(record.get("first_name") or "").strip()
    last = str(record.get("last_name") or "").strip()
    return f"{first} {last}".strip()


def suffix_stripped_key(name: str) -> str:
    parts = [part for part in name.replace(".", "").split() if part]
    if parts and parts[-1].casefold() in SUFFIXES:
        parts = parts[:-1]
    return normalized_asset_name(" ".join(parts))


def build_indexes(sleeper_players: dict[str, dict[str, object]]):
    exact: dict[str, list[tuple[str, dict[str, object]]]] = defaultdict(list)
    without_suffix: dict[str, list[tuple[str, dict[str, object]]]] = defaultdict(list)

    for player_id, record in sleeper_players.items():
        if not isinstance(record, dict):
            continue
        name = external_full_name(record)
        if not name:
            continue
        exact[normalized_asset_name(name)].append((str(player_id), record))
        without_suffix[suffix_stripped_key(name)].append((str(player_id), record))

    return exact, without_suffix


def record_position(record: dict[str, object]) -> str:
    return str(record.get("position") or "").upper().strip()


def record_team(record: dict[str, object]) -> str:
    return str(record.get("team") or "").upper().strip()


def position_matches(record: dict[str, object], player) -> bool:
    sleeper_position = record_position(record)
    fantasy_position = base_position(player.position).upper()
    return not sleeper_position or sleeper_position == fantasy_position


def team_matches(record: dict[str, object], player) -> bool:
    sleeper_team = record_team(record)
    fantasy_team = str(player.team or "").upper().strip()
    return not fantasy_team or not sleeper_team or sleeper_team == fantasy_team


def best_unique_candidate(candidates, player):
    """Return one safe candidate, allowing stale team data but never position conflicts."""
    position_candidates = [
        item for item in candidates if position_matches(item[1], player)
    ]

    exact_team = [
        item for item in position_candidates if team_matches(item[1], player)
    ]
    if len(exact_team) == 1:
        return exact_team[0], "position_team"

    # Team assignments can lag after trades/free agency. A unique name+position
    # match is still safe enough; multiple same-name players remain unmatched.
    if len(position_candidates) == 1:
        return position_candidates[0], "position_only"

    return None, "ambiguous"


def choose_match(player, exact_index, suffix_index):
    player_key = normalized_asset_name(player.name)

    alias_name = PLAYER_NAME_ALIASES.get(player_key)
    if alias_name:
        alias_candidates = exact_index.get(normalized_asset_name(alias_name), [])
        match, quality = best_unique_candidate(alias_candidates, player)
        if match is not None:
            return match, f"alias_{quality}"

    exact_candidates = exact_index.get(player_key, [])
    match, quality = best_unique_candidate(exact_candidates, player)
    if match is not None:
        return match, f"exact_{quality}"

    suffix_candidates = suffix_index.get(suffix_stripped_key(player.name), [])
    match, quality = best_unique_candidate(suffix_candidates, player)
    if match is not None:
        return match, f"suffix_{quality}"

    return None, "unmatched"


def save_headshot(image_bytes: bytes, destination: Path) -> None:
    try:
        from PIL import Image, ImageOps
    except ImportError as error:
        raise RuntimeError(
            "Pillow is required for the one-time asset importer. "
            "Install it with: python3 -m pip install Pillow"
        ) from error

    destination.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(io.BytesIO(image_bytes)) as image:
        image = image.convert("RGBA")
        image = ImageOps.fit(
            image,
            IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.50, 0.36),
        )
        image.save(destination, format="PNG", optimize=True)


def write_manifest(manifest: dict[str, object]) -> None:
    PLAYER_ASSETS_FILE.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and cache NFL player headshots for Gridiron AI."
    )
    parser.add_argument(
        "--refresh-player-map",
        action="store_true",
        help="Re-download Sleeper's NFL player map instead of using the cached copy.",
    )
    parser.add_argument(
        "--force-images",
        "--force",
        dest="force_images",
        action="store_true",
        help="Re-download headshots even when a cached image already exists.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N ranked players. Existing manifest entries are preserved.",
    )
    args = parser.parse_args()

    ensure_asset_directories()
    sleeper_players = load_sleeper_players(args.refresh_player_map)
    exact_index, suffix_index = build_indexes(sleeper_players)

    players = load_players()
    if args.limit is not None:
        players = players[: max(0, args.limit)]

    manifest = load_existing_manifest()
    manifest_players = manifest["players"]
    assert isinstance(manifest_players, dict)

    downloaded = 0
    cached = 0
    matched = 0
    team_assets = 0
    no_headshot = []
    real_failures = []
    unmatched = []

    for index, player in enumerate(players, start=1):
        player_key = normalized_asset_name(player.name)
        position = base_position(player.position).upper()

        # DST rows are franchise assets, not people. They belong in the team-logo
        # pipeline and should never hit a player-headshot endpoint.
        if position == "DST":
            team_assets += 1
            manifest_players[player_key] = {
                "display_name": player.name,
                "team": player.team,
                "position": position,
                "match_type": "team_asset",
                "headshot": None,
                "source_name": player.name,
            }
            print(f"[{index:>3}/{len(players)}] TEAM LOGO  {player.name}")
            continue

        match, match_type = choose_match(player, exact_index, suffix_index)
        if match is None:
            unmatched.append(f"{player.name} ({player.position}, {player.team})")
            print(f"[{index:>3}/{len(players)}] UNMATCHED  {player.name}")
            continue

        player_id, record = match
        matched += 1
        filename = f"{asset_filename(player.name)}.png"
        destination = HEADSHOTS_DIR / filename
        relative_path = destination.relative_to(ASSETS_DIR).as_posix()

        state = "OK"
        image_ok = False

        if destination.is_file() and not args.force_images:
            cached += 1
            image_ok = True
            state = "CACHED"
        else:
            try:
                image_bytes = fetch_bytes(
                    HEADSHOT_URL.format(player_id=player_id),
                    timeout=20,
                )
                save_headshot(image_bytes, destination)
                downloaded += 1
                image_ok = True
                state = "OK"
            except HTTPError as error:
                if error.code in {403, 404}:
                    # Sleeper knows the player but does not currently serve a usable
                    # image for this ID. This is expected for some rookies/depth players.
                    no_headshot.append(player.name)
                    state = "NO IMAGE"
                else:
                    real_failures.append(f"{player.name}: HTTP {error.code} {error.reason}")
                    state = "ERROR"
            except (URLError, TimeoutError, OSError, RuntimeError) as error:
                real_failures.append(f"{player.name}: {error}")
                state = "ERROR"

        manifest_players[player_key] = {
            "display_name": player.name,
            "sleeper_player_id": player_id,
            "team": player.team,
            "position": position,
            "match_type": match_type,
            "headshot": relative_path if image_ok else None,
            "source_name": external_full_name(record),
        }

        print(f"[{index:>3}/{len(players)}] {state:<9} {player.name}")

    write_manifest(manifest)

    print("\n================================")
    print(" GRIDIRON AI ASSET IMPORT")
    print("================================")
    print(f"Players processed:       {len(players)}")
    print(f"Matched players:         {matched}")
    print(f"Downloaded this run:     {downloaded}")
    print(f"Already cached:          {cached}")
    print(f"No headshot available:   {len(no_headshot)}")
    print(f"DST / team-logo rows:    {team_assets}")
    print(f"Unmatched:               {len(unmatched)}")
    print(f"True download errors:    {len(real_failures)}")
    print(f"Manifest:                {PLAYER_ASSETS_FILE}")

    if unmatched:
        print("\nUNMATCHED")
        for item in unmatched:
            print(f"- {item}")

    if no_headshot:
        print("\nNO HEADSHOT AVAILABLE")
        print("Sleeper matched these players but did not serve an image. Initials fallback will be used.")
        for item in no_headshot:
            print(f"- {item}")

    if real_failures:
        print("\nDOWNLOAD ERRORS")
        for item in real_failures:
            print(f"- {item}")


if __name__ == "__main__":
    main()
