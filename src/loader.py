import pandas as pd

from player import Player


def load_players(csv_path="../data/FantasyPros_2026_Draft_ALL_Rankings.csv"):

    df = pd.read_csv(csv_path)

    players = []

    for _, row in df.iterrows():

        # Skip rows that don't have a valid rank or tier
        try:
            rank = int(row["RK"])
            tier = int(row["TIERS"])
        except:
            continue

        # Handle missing bye weeks
        try:
            bye = int(row["BYE WEEK"])
        except:
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

    players.sort(key=lambda p: p.rank)

    return players