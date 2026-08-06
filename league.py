from team import Team


class League:
    def __init__(self, num_teams=10):

        self.num_teams = num_teams

        self.teams = []

        self.create_teams()

    def create_teams(self):

        for i in range(1, self.num_teams + 1):

            self.teams.append(Team(i))

    def print_teams(self):

        print()

        print("League Teams")

        print("----------------")

        for team in self.teams:

            print(f"Team {team.team_id}")