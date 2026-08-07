from pathlib import Path

import pandas as pd

from project_paths import MY_GUYS_FILE


def normalize_name(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


def load_my_guys(
    excel_path: str | Path = MY_GUYS_FILE,
) -> set[str]:
    path = Path(excel_path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(
            "My Guys spreadsheet was not found: "
            f"{path}"
        )

    dataframe = pd.read_excel(path)

    required_columns = {"Position", "Player", "Team", "Bye"}
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"My Guys.xlsx is missing columns: {missing_text}"
        )

    return {
        normalize_name(player_name)
        for player_name in dataframe["Player"].dropna()
    }
