from pathlib import Path

import pandas as pd

from preferences import normalize_name
from projection import Projection


DATA_FOLDER = Path("../data")

PROJECTION_FILES = {
    "QB": "FantasyPros_Fantasy_Football_Projections_QB.csv",
    "RB": "FantasyPros_Fantasy_Football_Projections_RB.csv",
    "WR": "FantasyPros_Fantasy_Football_Projections_WR.csv",
    "TE": "FantasyPros_Fantasy_Football_Projections_TE.csv",
    "K": "FantasyPros_Fantasy_Football_Projections_K.csv",
    "DST": "FantasyPros_Fantasy_Football_Projections_DST.csv",
}


def numeric_value(value: object) -> float:
    if pd.isna(value):
        return 0.0

    cleaned = str(value).strip().replace(",", "")

    if cleaned in {"", "-", "N/A", "nan"}:
        return 0.0

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def row_stats(
    row: pd.Series,
    position: str,
) -> dict[str, float]:
    if position == "QB":
        return {
            "passing_attempts": numeric_value(row.get("ATT")),
            "passing_completions": numeric_value(row.get("CMP")),
            "passing_yards": numeric_value(row.get("YDS")),
            "passing_touchdowns": numeric_value(row.get("TDS")),
            "interceptions": numeric_value(row.get("INTS")),
            "rushing_attempts": numeric_value(row.get("ATT.1")),
            "rushing_yards": numeric_value(row.get("YDS.1")),
            "rushing_touchdowns": numeric_value(row.get("TDS.1")),
            "fumbles_lost": numeric_value(row.get("FL")),
        }

    if position == "RB":
        return {
            "rushing_attempts": numeric_value(row.get("ATT")),
            "rushing_yards": numeric_value(row.get("YDS")),
            "rushing_touchdowns": numeric_value(row.get("TDS")),
            "receptions": numeric_value(row.get("REC")),
            "receiving_yards": numeric_value(row.get("YDS.1")),
            "receiving_touchdowns": numeric_value(row.get("TDS.1")),
            "fumbles_lost": numeric_value(row.get("FL")),
        }

    if position == "WR":
        return {
            "receptions": numeric_value(row.get("REC")),
            "receiving_yards": numeric_value(row.get("YDS")),
            "receiving_touchdowns": numeric_value(row.get("TDS")),
            "rushing_attempts": numeric_value(row.get("ATT")),
            "rushing_yards": numeric_value(row.get("YDS.1")),
            "rushing_touchdowns": numeric_value(row.get("TDS.1")),
            "fumbles_lost": numeric_value(row.get("FL")),
        }

    if position == "TE":
        return {
            "receptions": numeric_value(row.get("REC")),
            "receiving_yards": numeric_value(row.get("YDS")),
            "receiving_touchdowns": numeric_value(row.get("TDS")),
            "fumbles_lost": numeric_value(row.get("FL")),
        }

    if position == "K":
        return {
            "field_goals_made": numeric_value(row.get("FG")),
            "field_goals_attempted": numeric_value(row.get("FGA")),
            "extra_points_made": numeric_value(row.get("XPT")),
        }

    if position == "DST":
        return {
            "sacks": numeric_value(row.get("SACK")),
            "interceptions": numeric_value(row.get("INT")),
            "fumble_recoveries": numeric_value(row.get("FR")),
            "forced_fumbles": numeric_value(row.get("FF")),
            "touchdowns": numeric_value(row.get("TD")),
            "safeties": numeric_value(row.get("SAFETY")),
            "points_allowed": numeric_value(row.get("PA")),
            "yards_allowed": numeric_value(row.get("YDS_AGN")),
        }

    return {}


def load_projection_file(
    position: str,
    filename: str,
) -> list[Projection]:
    path = DATA_FOLDER / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Projection file was not found: {path}"
        )

    dataframe = pd.read_csv(path)

    # FantasyPros files include a blank spacer row.
    dataframe = dataframe.dropna(
        subset=["Player"],
    )

    projections: list[Projection] = []

    for _, row in dataframe.iterrows():
        name = str(row["Player"]).strip()

        if not name:
            continue

        team_value = row.get("Team", "")
        team = "" if pd.isna(team_value) else str(team_value).strip()

        projection = Projection(
            name=name,
            position=position,
            team=team,
            fantasy_points=numeric_value(row.get("FPTS")),
            stats=row_stats(row, position),
        )

        projections.append(projection)

    return projections


def load_projections() -> dict[str, Projection]:
    projections: dict[str, Projection] = {}

    for position, filename in PROJECTION_FILES.items():
        position_projections = load_projection_file(
            position=position,
            filename=filename,
        )

        for projection in position_projections:
            key = normalize_name(projection.name)
            projections[key] = projection

    return projections