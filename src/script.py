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
district_colors = {
    "1": "red",
    "2": "blue"
}

class GerrymanderingMCMC(): 
    def __init__(self, path_graph, cooling_period=50, rounds=200): 
        # We initialize all_districts here, but we really establish it when we read our graph in
        self.all_districts = set()
        self.g = self.read_graph(path_graph)
        self.cooling_period = cooling_period
        self.rounds = rounds

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
            winning_group = ""
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
        return [district_colors[g.nodes[n]["district"]] for n in g.nodes]

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

    def __is_valid_mst(self, edge, mst_combined_subgraph, g):
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
        self.__drawGraph(comp_1)
        comp_2 = g.subgraph(components[1])
        self.__drawGraph(comp_2)
        for node in comp_1.nodes:
            g.nodes[node]["district"] = d1
        for node in comp_2.nodes:
            g.nodes[node]["district"] = d2

    def recombination_of_districts(self):
        """
            Given a graph
            Perform the recombination algorithm described in https://mggg.org/va-report.pdf
            (Metric Geometry and Gerrymandering Group, Comparison of Districting Plans for the Virginia House of Delegates; Section 2.3.2)
            Alternative resource: the recombination algorithm described in https://arxiv.org/pdf/1911.05725.pdf
            (Recombination: A family of Markov chains for redistricting - Daryl DeFord, Moon Duchin, and Justin Solomon)
        """
        # Randomly sample a district
        d1 = str(random.randint(1, len(self.all_districts)))
        # Select one of its neighboring districts
        d2 = self.__find_neighboring_district(d1)
        d2_nodes = self.__get_district_nodes(self.g, d2)
        d1_nodes = self.__get_district_nodes(self.g, d1)
        combined_subgraph = self.g.subgraph(d1_nodes + d2_nodes)
        cuttable = False
        print("Trying to find a cut")
        attempt_count = 0
        while cuttable is False:
            mst_combined_subgraph =  self.__random_spanning_tree(combined_subgraph)
            self.__drawGraph(mst_combined_subgraph)
            # For all edges in the MST
            for edge in mst_combined_subgraph.edges:
                # NOTE: Just print somewhat regularly for outputs sake - helps detect infinite loops
                print("... ", attempt_count) if attempt_count % 10 == 0 else None
                cond = self.__is_valid_mst(edge, mst_combined_subgraph, self.g)
                if (cond):
                    cuttable = True
                    print("WE HAVE A WINNER")
                    self.__update_new_districts_with_cut(edge, mst_combined_subgraph, self.g, d1, d2)
                    self.__drawGraph(self.g)
                    return edge
                if (attempt_count == self.rounds):
                    return
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

    def generate_alternative_plans(self):
        # Draw the graph initially
        self.__drawGraph(self.g)

        """
        For cooling many runs: 
            -  ReCom the graph that many times
        For rounds many runs 
            - ReCom the graph
            - Record the relevant statistics: 
                - Efficiency gap
                - Total D votes counted
                - Total R votes counted
            - If run % 50 === 0 
                print to the screen
            - If run === 5 || 50 || 500
                Draw the graph
        Graph the results of this run
            - PLot 
        Save the graphs to disk with a unique file name
        """

        for d_label in self.all_districts:
            d_graph = self.__get_district_subgraph(self.g, d_label)
            eg = self.__efficiency_gap(d_graph)
            print(eg)

        print("Recom")
        print("==========")
        self.recombination_of_districts()


def main():
    parser = argparse.ArgumentParser(description='Use MCMC Simulation to determine the likelihood that a particular district is an outlier by the efficiency gap metric')
    parser.add_argument("-f", "--file", default=default_file)
    parser.add_argument("-r", "--rounds", type=int, default=50)
    args = parser.parse_args()

    file = args.file
    rounds = args.rounds

    mcmc = GerrymanderingMCMC(file, rounds=rounds)
    mcmc.generate_alternative_plans()

if __name__ == "__main__":
    main()
