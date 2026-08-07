from pathlib import Path

import pandas as pd


MY_GUYS_FILE = Path("../data/My Guys.xlsx")


def normalize_name(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


def load_my_guys(
    excel_path: Path = MY_GUYS_FILE,
) -> set[str]:
    dataframe = pd.read_excel(excel_path)

    required_columns = {"Position", "Player", "Team", "Bye"}
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"My Guys.xlsx is missing columns: {missing_text}"
        )

    names = {
        normalize_name(player_name)
        for player_name in dataframe["Player"].dropna()
    }

    return names