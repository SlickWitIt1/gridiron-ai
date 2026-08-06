from simulation import Simulation


def main():

    print("===================================")
    print(" Taylor Draft Simulator")
    print("===================================")

    simulation = Simulation()

    simulation.run()

    print("\nFINAL ROSTERS")

    for team in simulation.league.teams:

        team.print_roster()


if __name__ == "__main__":
    main()