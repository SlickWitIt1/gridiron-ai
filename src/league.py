from team import Team


class League:

    def __init__(self, num_teams=10, num_rounds=16):

        self.num_teams = num_teams
        self.num_rounds = num_rounds

        self.teams = []
        self.draft_order = []

        self.create_teams()
        self.create_draft_order()

    def create_teams(self):

        for i in range(1, self.num_teams + 1):
            self.teams.append(Team(i))

    def create_draft_order(self):

        self.draft_order = []

        for round_num in range(1, self.num_rounds + 1):

            if round_num % 2 == 1:
                # Odd rounds
                self.draft_order.extend(range(1, self.num_teams + 1))
            else:
                # Even rounds
                self.draft_order.extend(range(self.num_teams, 0, -1))

    def print_draft_order(self):

        for round_num in range(self.num_rounds):

            print(f"\nRound {round_num + 1}")

            start = round_num * self.num_teams
            end = start + self.num_teams

            print(self.draft_order[start:end])