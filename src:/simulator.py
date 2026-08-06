import pandas as pd
from pathlib import Path


# -------------------------------------------------
# Configuration
# -------------------------------------------------

DATA_FOLDER = Path("../data")

FANTASYPROS_FILE = DATA_FOLDER / "FantasyPros_2026_Draft_ALL_Rankings.csv"
MY_GUYS_FILE = DATA_FOLDER / "My Guys.xlsx"


# -------------------------------------------------
# Load FantasyPros Rankings
# -------------------------------------------------

def load_fantasypros():

    print("Loading FantasyPros rankings...")

    df = pd.read_csv(FANTASYPROS_FILE)

    print(f"Loaded {len(df)} FantasyPros players.")

    return df


# -------------------------------------------------
# Load My Guys
# -------------------------------------------------

def load_my_guys():

    print("Loading My Guys...")

    df = pd.read_excel(MY_GUYS_FILE)

    print(f"Loaded {len(df)} preferred players.")

    return df


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():

    fantasypros = load_fantasypros()

    my_guys = load_my_guys()

    print()

    print("FantasyPros Preview")

    print(fantasypros.head())

    print()

    print("My Guys Preview")

    print(my_guys.head())


if __name__ == "__main__":
    main()
