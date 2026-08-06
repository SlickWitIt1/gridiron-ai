from player import Player


class Team:

    STARTERS = {
        "QB": 1,
        "RB": 2,
        "WR": 2,
        "TE": 1,
        "DST": 1,
        "K": 1,
    }

    BENCH_SIZE = 7

    def __init__(self, number):

        self.number = number
        self.players = []

    def add_player(self, player):

        self.players.append(player)

    def count_position(self, position):

        return sum(
            1
            for player in self.players
            if player.position.startswith(position)
        )

    def starter_slots_filled(self):

        total = 0

        for position, limit in self.STARTERS.items():

            total += min(self.count_position(position), limit)

        return total

    def bench_players(self):

        return max(0, len(self.players) - self.starter_slots_filled())

    def needs_position(self, position):

        # Fill starters first
        if position in self.STARTERS:

            if self.count_position(position) < self.STARTERS[position]:
                return True

        # After starters are full...
        if self.starter_slots_filled() >= 8:

            if self.bench_players() < self.BENCH_SIZE:
                return True

        return False

    def print_roster(self):

        print("\n" + "=" * 35)
        print(f"TEAM {self.number}")
        print("=" * 35)

        for player in self.players:
            print(player)