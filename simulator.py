from monte_carlo import MonteCarloRunner


def main():

    print("===================================")
    print("         GRIDIRON AI")
    print("===================================")

    print("\nRunning Monte Carlo...\n")

    runner = MonteCarloRunner()

    results = runner.run(
        simulations=100,
    )

    print("=" * 40)
    print(" MONTE CARLO RESULTS")
    print("=" * 40)

    print(
        f"Simulations : {results.simulations}"
    )

    print(
        f"Average     : {results.average_projection:.1f}"
    )

    print(
        f"Best        : {results.best_projection:.1f}"
    )

    print(
        f"Worst       : {results.worst_projection:.1f}"
    )


if __name__ == "__main__":
    main()