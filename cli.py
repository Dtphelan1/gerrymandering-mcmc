import argparse
from src.GerrymanderingMCMC import GerrymanderingMCMC

default_file = "./src/data/iowa.json"

def main():
    parser = argparse.ArgumentParser(description='Use MCMC Simulation to determine the likelihood that a particular district is an outlier by the efficiency gap metric')
    parser.add_argument("-g", "--graph_file", default=default_file, help="A path to a potential districting plan specified in this projects proprietary json schema")
    parser.add_argument("-c", "--cooling_period", type=int, default=50, help="The number of plans you'd like to generate _before_ counting them towards your ensemble; defaults to 50")
    parser.add_argument("-r", "--rounds", type=int, default=200, help="The number of plans you'd like to generate and include in your ensemble; defaults to 200")
    parser.add_argument("-v", "--verbose", action="store_true", help="Include this flag if you'd like real-time output to the console")
    args = parser.parse_args()

    graph_file = args.graph_file
    cooling_period = args.cooling_period
    rounds = args.rounds
    verbose = args.verbose

    mcmc = GerrymanderingMCMC(graph_file, cooling_period=cooling_period, rounds=rounds, verbose=verbose)
    mcmc.generate_alternative_plans()

    # Plot the data for the results of the recombinations
    mcmc.plot_data()

    # Save the data
if __name__ == "__main__":
    main()

