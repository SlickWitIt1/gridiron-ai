from pathlib import Path

import pandas as pd

from player import Player
from project_paths import RANKINGS_FILE


def load_players(
    csv_path: str | Path = RANKINGS_FILE,
) -> list[Player]:
    path = Path(csv_path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(
            "FantasyPros rankings file was not found: "
            f"{path}"
        )

    dataframe = pd.read_csv(path)
    players: list[Player] = []

    for _, row in dataframe.iterrows():
        try:
            rank = int(row["RK"])
            tier = int(row["TIERS"])
        except (KeyError, TypeError, ValueError):
            continue

        try:
            bye = int(row["BYE WEEK"])
        except (KeyError, TypeError, ValueError):
            bye = 0

        player = Player(
            rank=rank,
            tier=tier,
            name=str(row["PLAYER NAME"]).strip(),
            position=str(row["POS"]).strip(),
            team=str(row["TEAM"]).strip(),
            bye=bye,
            upside=str(row["UPSIDE "]).strip(),
            bust=str(row["BUST "]).strip(),
            sos=str(row["SOS SEASON"]).strip(),
        )

        players.append(player)

    players.sort(key=lambda player: player.rank)
    return players
