from team import Team


def main():

    team = Team(1)

    print(team.needs_position("QB"))

    print(team.count_position("QB"))


if __name__ == "__main__":
    main()