from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"

MY_GUYS_FILE = DATA_DIR / "My Guys.xlsx"
RANKINGS_FILE = DATA_DIR / "FantasyPros_2026_Draft_ALL_Rankings.csv"
LIVE_DRAFT_SAVE_FILE = OUTPUT_DIR / "live_draft_session.json"

PROJECTION_FILES = {
    "QB": DATA_DIR / "FantasyPros_Fantasy_Football_Projections_QB.csv",
    "RB": DATA_DIR / "FantasyPros_Fantasy_Football_Projections_RB.csv",
    "WR": DATA_DIR / "FantasyPros_Fantasy_Football_Projections_WR.csv",
    "TE": DATA_DIR / "FantasyPros_Fantasy_Football_Projections_TE.csv",
    "K": DATA_DIR / "FantasyPros_Fantasy_Football_Projections_K.csv",
    "DST": DATA_DIR / "FantasyPros_Fantasy_Football_Projections_DST.csv",
}


def required_data_files() -> tuple[Path, ...]:
    return (
        MY_GUYS_FILE,
        RANKINGS_FILE,
        *PROJECTION_FILES.values(),
    )


def missing_data_files() -> tuple[Path, ...]:
    return tuple(
        path
        for path in required_data_files()
        if not path.is_file()
    )


def validate_data_files() -> None:
    missing = missing_data_files()

    if not missing:
        return

    missing_list = "\n".join(
        f"- {path}"
        for path in missing
    )

    raise FileNotFoundError(
        "Gridiron AI could not find these required data files:\n"
        f"{missing_list}\n\n"
        f"Expected data folder: {DATA_DIR}"
    )
