from league import League


def main():

    print("=========================================")
    print("      Taylor Draft Simulator v0.1")
    print("=========================================\n")

    league = League()

    print(f"League created with {league.num_teams} teams.\n")

    league.print_teams()


if __name__ == "__main__":
    main()