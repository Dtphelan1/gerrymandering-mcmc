from pathlib import Path
import json
import random
import networkx as nx
from networkx.algorithms import tree
import matplotlib.pyplot as plt
from functools import reduce
import argparse

# Globals we care about
default_file = "./data/precint-data.json"
MAX_POP_DIFFERENCE_PERCENTAGE = .05

class GerrymanderingMCMC():
    def __init__(self, graph_file, cooling_period=50, rounds=200, verbose=False):
        # We initialize all_districts here, but we really establish it when we read our graph in
        self.all_districts = set()
        self.g = self.read_graph(graph_file)
        self.cooling_period = cooling_period
        self.rounds = rounds
        self.verbose = verbose
        self.district_colors = {
            "1": "red",
            "2": "blue"
        }
        self.data = []
        self.original_data = {}
        self.__record_key_stats(self.g, is_original_plan=True)

    def read_graph(self, path):
        """
            Given a path to an specialized JSON format describing a graph and it's metadata
            Returns a nx.Graph with relevant metadata stored on the node objects
        """
        g = nx.Graph()
        node_data = self.__load_json(path)
        for node_label in node_data:
            # Read in nodes from json format
            g.add_node(node_label)
            for adj_node in node_data[node_label]["adjacent_nodes"]:
                g.add_edge(node_label, adj_node)
            g.nodes[node_label]["population"] = node_data[node_label]["population"]
            g.nodes[node_label]["voting_history"] = node_data[node_label]["voting_history"]
            g.nodes[node_label]["district"] = node_data[node_label]["district"]
            self.all_districts.add(node_data[node_label]["district"])
        return g

    def __load_json(self, path):
        """
            Loads a json file at a particular file-path location (str)
            Returns a json object corresponding to the data at the specified path
        """
        with Path(path).open() as json_file:
            return json.load(json_file)

    def __efficiency_gap(self, district_graph):
        """
            Determines the efficiency gap for a given district, and for whom it is in favor
            NOTE: Currently assumes a two-party system because plurality voting is the status quo; I'll improve the code when we improve our voting system
        """
        d_votes = r_votes = winning_votes = losing_votes = 0.00
        winning_group = ""
        # Total vote for a representative is just the number of precincts there are - the number of nodes on the graph
        total_votes = len(district_graph.nodes)
        # Plurality voting would mean that we wouldn't even need this many votes if more than two systems were relevant players;
        #   but plurality voting also has a funny way of pushing elections towards two-party systems - so let's just assume that
        #   only two parties matter and therefore 50% of the precincts are needed
        votes_to_win = total_votes/2

        # Tally total votes based on the precincts voting history
        # NOTE: If we wanted to introduce some interderminism, there could be distribution here
        for precint_label in district_graph.nodes:
            precint = district_graph.nodes[precint_label]
            if precint["voting_history"] == "D":
                d_votes += 1
            elif precint["voting_history"] == "R":
                r_votes += 1

        # Determine who the wining_group is and what the efficiency gap is
        if d_votes > r_votes:
            winning_group = "D"
            winning_votes = d_votes
            losing_votes = r_votes
        elif r_votes > d_votes:
            winning_group = "R"
            winning_votes = r_votes
            losing_votes = d_votes
        else:
            # TODO: Figure out what to do in the case of a tie; probably resample here
            winning_group = None
            efficiency_gap = 0
            return (efficiency_gap, winning_group)

        # RE: The calculation:
        # - All votes for a losing party are wasted
        # - Any superflous votes for the winning party are wasted
        # - Efficiency gap is a measure of how many more votes the losing party wasted than the winning party
        winning_votes_wasted = winning_votes - votes_to_win
        losing_votes_wasted = losing_votes
        efficiency_gap = (losing_votes_wasted - winning_votes_wasted) / total_votes
        return (efficiency_gap, winning_group)

    def __find_neighboring_district(self, district):
        """
            Given a district, find a district that neighbors it
            TODO: Do this meaningfully with node_boundary
        """
        return "2" if district == "1" else "1"

    def __get_district_nodes(self, g, district_label):
        """
            Given a nx.graph and a district_label
            Return a list of all the precincts (nodes) in that district
        """
        return [n for n in g.nodes if g.nodes[n]["district"] == district_label]

    def __get_node_colors(self, g):
        return [self.district_colors[g.nodes[n]["district"]] for n in g.nodes]

    def __get_district_subgraph(self, g, district_label):
        """
            Given a nx.graph and a district_label
            Return a subgraph view (not clone) corresponding to the precincts in that district
        """
        relevant_nodes = self.__get_district_nodes(g, district_label)
        return g.subgraph(relevant_nodes)

    def __district_size(self, potential_district):
        """
            Given a potential district of nodes, using the population size of the district
            Return the population size of the district
        """
        return reduce(lambda total, precinct: total + int(potential_district.nodes[precinct]["population"]), potential_district.nodes(), 0)

    def __is_valid_districting(self, edge, mst_combined_subgraph, g):
        """
            For a given potential edge cut on an MST in the ReCom algorithm,
            Determine whether a series of required conditions is satisfied, including:
                1. Population size after new districting,
        """
        # 1. Check the population size after this cut
        # Does cutting this edges create two components with similar population sizes?
        (tail, head) = edge
        mst_combined_subgraph.remove_edge(tail, head)
        components = list(nx.connected_components(mst_combined_subgraph))
        comp_1 = g.subgraph(components[0])
        comp_2 = g.subgraph(components[1])
        pop_total = abs(self.__district_size(comp_1) + self.__district_size(comp_2))
        pop_diff = abs(self.__district_size(comp_1) - self.__district_size(comp_2))
        # Add edge back in case this doesn't work
        mst_combined_subgraph.add_edge(tail, head)
        return pop_diff < (MAX_POP_DIFFERENCE_PERCENTAGE*pop_total)

    def __update_new_districts_with_cut(self, edge, mst_combined_subgraph, g, d1, d2):
        """
            After chcecking that an edge chould be cut to create new districts after combining into a single mega-district
            Redistrict the new components accordingly
        """
        (tail, head) = edge
        mst_combined_subgraph.remove_edge(tail, head)
        components = list(nx.connected_components(mst_combined_subgraph))
        comp_1 = g.subgraph(components[0])
        comp_2 = g.subgraph(components[1])
        for node in comp_1.nodes:
            g.nodes[node]["district"] = d1
        for node in comp_2.nodes:
            g.nodes[node]["district"] = d2

    def recombination_of_districts(self, i):
        """
            Given a graph
            Perform the recombination algorithm described in https://mggg.org/va-report.pdf
            (Metric Geometry and Gerrymandering Group, Comparison of Districting Plans for the Virginia House of Delegates; Section 2.3.2)
            Alternative resource: the recombination algorithm described in https://arxiv.org/pdf/1911.05725.pdf
            (Recombination: A family of Markov chains for redistricting - Daryl DeFord, Moon Duchin, and Justin Solomon)
        """
        graph = self.g.copy()
        # Randomly sample a district
        d1 = str(random.randint(1, len(self.all_districts)))
        d1_nodes = self.__get_district_nodes(graph, d1)
        # Select one of its neighboring districts
        d2 = self.__find_neighboring_district(d1)
        d2_nodes = self.__get_district_nodes(graph, d2)
        combined_subgraph = graph.subgraph(d1_nodes + d2_nodes)
        cuttable = False
        attempt_count = 0
        while cuttable is False:
            mst_combined_subgraph =  self.__random_spanning_tree(combined_subgraph)
            # For all edges in the MST
            for edge in mst_combined_subgraph.edges:
                # If cutting this edge produces a valid districting
                cond = self.__is_valid_districting(edge, mst_combined_subgraph, graph)
                if (cond):
                    cuttable = True
                    self.__update_new_districts_with_cut(edge, mst_combined_subgraph, graph, d1, d2)
                    return graph
                if (attempt_count == 1000):
                    print("WARNING: Failed to make a recom after > 1000 iterations") if self.verbose else None
                    return graph
                else:
                    attempt_count += 1
                    (tail, head) = edge
                    mst_combined_subgraph.add_edge(tail, head)

    def __drawGraph(self, G, options=None):
        """
            Given a graph, plot and draw it with these default options, or with options
        """

        node_colors = self.__get_node_colors(G)
        options = options if options != None else {
            'node_color': node_colors,
            'node_size': 100,
            "with_labels":True,
            'width': 3,
            "font_weight": "bold"
        }
        plt.subplot(222)

        # Draw the graph we've been provided
        nx.draw_networkx(G, **options)
        plt.show()

    def __random_spanning_tree(self, graph):
        """
            Given a graph
            Return a random spanning tree
        """
        for edge in graph.edges:
            graph.edges[edge]["weight"] = random.random()

        spanning_tree = tree.maximum_spanning_tree(
            graph, algorithm="kruskal", weight="weight"
        )
        return spanning_tree

    def __record_key_stats(self, graph, is_original_plan=False):
        """
            Given a potential districting plan (graph) and an optional flag for saying this is the original plan,
            Update our local data record to include stats for this plan
        """
        data_obj = {}
        data_obj["eg"] = self.__efficiency_gap(graph)[0]
        data_obj["d_districts"] = self.__count_votes(graph, "D")
        data_obj["r_districts"] = self.__count_votes(graph, "R")
        self.data.append(data_obj)

    def __winning_party_for_district(self, graph, district_label):
        """
            Given a graph and a district label,
            Return the party with the most precint votes
        """
        district = self.__get_district_subgraph(graph, district_label)
        # TODO: Update to use more than two parties
        demo_count = reduce(lambda demo_count, n_label: demo_count + 1 if district.nodes[n_label]["voting_history"] == "D" else demo_count - 1 , district.nodes, 0)
        if demo_count == 0:
            return None
        elif demo_count < 0:
            return "R"
        else:
            return "D"

    def __count_votes(self, graph, party):
        """
            Given a graph and party,
            Return the number of districts that voted for that party
        """
        return reduce(lambda count, d_label: count + 1 if self.__winning_party_for_district(graph, d_label) == party else count , self.all_districts, 0)

    def plot_data(self):
        print(self.data) if self.verbose else None
        plt.hist([d["eg"] for d in self.data], bins="auto", facecolor='blue')
        plt.title("Efficiency Gap")
        plt.show()
        plt.hist([d["d_districts"] for d in self.data], bins="auto", facecolor='blue')
        plt.title("Democratic Districts")
        plt.show()
        plt.hist([d["r_districts"] for d in self.data], bins="auto", facecolor='blue')
        plt.title("Republican Districts")
        plt.show()

    def generate_alternative_plans(self):
        # Draw the graph initially
        self.__drawGraph(self.g) if self.verbose else None

        print ()

        # Run `cooling`-many rounds to randomize the plan a bit
        for i in range(0, self.cooling_period):
            print("Randomizing the seed plan", i ) if i % 25 == 0 and self.verbose else None
            self.recombination_of_districts(i)

        # Run `rounds`-many recombinations to build a distribution of a few key stats
        for i in range(0, self.rounds):
            print("Finding recomb ... ", i ) if i % 10 == 0 and self.verbose else None
            graph = self.recombination_of_districts(i)
            self.__record_key_stats(graph)



def main():
    parser = argparse.ArgumentParser(description='Use MCMC Simulation to determine the likelihood that a particular district is an outlier by the efficiency gap metric')
    parser.add_argument("-g", "--graph_file", default=default_file)
    parser.add_argument("-r", "--rounds", type=int, default=50)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    graph_file = args.graph_file
    rounds = args.rounds
    verbose = args.verbose

    mcmc = GerrymanderingMCMC(graph_file, rounds=rounds, verbose=verbose)
    mcmc.generate_alternative_plans()

    # Plot the data for the results of the recombinations
    mcmc.plot_data()

    # Save the data
if __name__ == "__main__":
    main()
