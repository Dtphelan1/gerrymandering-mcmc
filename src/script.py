from pathlib import Path
import json
import random
import networkx as nx
import matplotlib.pyplot as plt
from functools import reduce
import argparse

# Globals we care about
path_adjlist = "./data/adjlist.txt"
path_edgelist = "./data/edgelist.txt"
path_shpfile = "./data/stations/stations.shp"
path_metadata = "./data/precint-data.json"
MAX_POP_DIFFERENCE_PERCENTAGE = .1
MAX_ATTEMPTS = 400
all_districts = ["1", "2"]
district_colors = {
    "1": "red",
    "2": "blue"
}
file_lookup_table = {
    "adj": path_adjlist,
    "edge": path_edgelist,
    "shp": path_shpfile
}

def import_graph(path_graph, path_metadata, ignore_meta=False):
    """
        Given a path to an adj_list/edge_list file describing a graph,
            and a path to a metadata file describing relevant information about precints
        Returns a nx.Graph with relevant metadata stored on the node objects
    """
    try:
        g = nx.read_adjlist(path_graph)
    except:
        # g = nx.read_edgelist(path_graph)
        g = nx.read_shp(path_graph)

    if not ignore_meta:
        metadata = load_json(path_metadata)
        for node_label in metadata:
            g.nodes[node_label]["population"] = metadata[node_label]["population"]
            g.nodes[node_label]["voting_history"] = metadata[node_label]["voting_history"]
            g.nodes[node_label]["district"] = metadata[node_label]["district"]
    return g


def load_json(path):
    """
        Loads a json file at a particular file-path location (str)
        Returns a json object corresponding to the data at the specified path
    """
    with Path(path).open() as json_file:
        return json.load(json_file)


def efficiency_gap(district_graph):
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


# def find_neighboring_district(graph, district_subgraph):
def find_neighboring_district(district):
    """
        Given a district, find a district that neighbors it
        TODO: Do this meaningfully
    """
    return "2" if district == "1" else "1"


def get_district_nodes(g, district_label):
    """
        Given a nx.graph and a district_label
        Return a list of all the precincts (nodes) in that district
    """
    return [n for n in g.nodes if g.nodes[n]["district"] == district_label]


def get_node_colors(g):
    return [district_colors[g.nodes[n]["district"]] for n in g.nodes]


def get_district_subgraph(g, district_label):
    """
        Given a nx.graph and a district_label
        Return a subgraph view (not clone) corresponding to the precincts in that district
    """
    relevant_nodes = get_district_nodes(g, district_label)
    return g.subgraph(relevant_nodes)


def district_size(potential_district):
    """
        Given a potential district of nodes,
        Return the population size of the district
    """
    return reduce(lambda total, precinct: total + int(potential_district.nodes[precinct]["population"]), potential_district.nodes(), 0)


def recombination_of_districts(g):
    """
        Given a graph
        Perform the recombination algorithm described in https://mggg.org/va-report.pdf
        (Metric Geometry and Gerrymandering Group, Comparison of Districting Plans for the Virginia House of Delegates; Section 2.3.2)
    """
    # Randomly sample a district
    d1 = str(random.randint(1, len(all_districts)))
    # Select one of its neighboring districts
    d2 = find_neighboring_district(d1)
    d1_nodes = get_district_nodes(g, d1)
    d2_nodes = get_district_nodes(g, d2)
    combined_subgraph = nx.Graph(g.subgraph(d1_nodes + d2_nodes))
    cuttable = False
    print("Trying to find a cut")
    attempt_count = 0
    while cuttable is False:
        # NOTE: Have to use PRIM's here becuase Kruskal's will return the same MST every time.
        # mst_combined_subgraph =  nx.minimum_spanning_tree(combined_subgraph)
        mst_combined_subgraph =  nx.minimum_spanning_tree(combined_subgraph, algorithm="prim")
        drawGraph(mst_combined_subgraph)
        # For all edges in the MST
        print(MAX_POP_DIFFERENCE_PERCENTAGE*district_size(combined_subgraph))
        for (tail, head) in mst_combined_subgraph.edges:
            # Does cutting this edges create two components with similar population sizes?
            mst_combined_subgraph.remove_edge(tail, head)
            components = list(nx.connected_components(mst_combined_subgraph))
            comp_1 = g.subgraph(components[0])
            comp_2 = g.subgraph(components[1])
            pop_diff = abs(district_size(comp_1) - district_size(comp_2))
            print("... ", attempt_count) if attempt_count % 10 == 0 else None
            if (pop_diff < MAX_POP_DIFFERENCE_PERCENTAGE*district_size(combined_subgraph)):
                print("Cutting edge: ", tail, head)
                print(components)
                print(pop_diff)
                cuttable = True
                print("WE HAVE A WINNER")
                return (tail, head)
            if (attempt_count == MAX_ATTEMPTS):
                return
            else:
                attempt_count += 1
                mst_combined_subgraph.add_edge(tail, head)

# ReCom Algo:

# - Look at the subgraph induced by the vertices in both districts
# - Make an MST for the graph
#     - Does cutting this edges create two components with similar population sizes
#         (for subcomponents created by the edge cut, calculat the total population and compare with a delta)
#     - YES:
#         Done - keep cut
#     - NO:
#         - continue iterating through edges
# - Redistrict along that edge cut


def drawGraph(G, options=None):
    """
        Given a graph, plot and draw it with these default options, or with options
    """

    node_colors = get_node_colors(G)
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

def main():
    parser = argparse.ArgumentParser(description='Use MCMC Simulation to determine the likelihood that a particular district is an outlier by the efficiency gap metric')
    parser.add_argument("file")
    args = parser.parse_args()

    path = file_lookup_table[args.file]

    g = import_graph(path, path_metadata, ignore_meta=(args.file == "shp"))
    drawGraph(g)

    # For all districts, draw the graph
    # for d_obj in all_districts:
    #     d = get_district_subgraph(g, d_obj.label)
    #     eg = efficiency_gap(d)
    #     print(eg)

    # print("Recomb")
    # print("==========")
    # recombination_of_districts(g, all_districts)

if __name__ == "__main__":
    main()
