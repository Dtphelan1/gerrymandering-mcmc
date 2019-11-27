from pathlib import Path
import json
import random
import networkx as nx
import matplotlib.pyplot as plt

# Path to the relevant file we're testing 
path_adjlist = "./data/adjlist.txt"
path_metadata = "./data/precint-data.json"
MAX_POP_DIFFERENCE = 15

# Read in and import the data we care about 
def import_graph(path_adjlist, path_metadata):
    g = nx.read_adjlist(path_adjlist)
    metadata = read_metadata(path_metadata)
    for node_label in metadata: 
        g.nodes[node_label]["population"] = metadata[node_label]["population"]
        g.nodes[node_label]["voting_history"] = metadata[node_label]["voting_history"]
        g.nodes[node_label]["district"] = metadata[node_label]["district"]
    return g

def read_metadata(path):
    with Path(path).open() as json_file:
        return json.load(json_file)

def efficiency_gap(district_graph):
    """
        Determines the efficiency gap for a given district, and for whom it is in favor
    """
    d_votes = r_votes = winning_votes = losing_votes = 0.00
    winning_group = ""
    total_votes = len(district_graph.nodes)
    votes_to_win = total_votes/2

    # Tally total votes
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
        # TODO: Figure out what to do in the case of a tie
        winning_group = ""
        efficiency_gap = 0 
        return (efficiency_gap, winning_group)

    # RE: The calculation: 
    # - All votes for a losing candidate are wasted .
    # - Any superflous votes for the winning candidate are wasted
    # - Efficiency gap is
    winning_votes_wasted = winning_votes - votes_to_win
    losing_votes_wasted = losing_votes
    efficiency_gap = (losing_votes_wasted - winning_votes_wasted) / total_votes
    return (efficiency_gap, winning_group)

def find_neighboring_district(district):
    """
        Given a district, find a district that neighbors it
    """ 
    return "2" if district == "1" else "1"

def get_district_nodes(g, district_label):
    return [n for n in g.nodes if g.nodes[n]["district"] == district_label]

def get_district_subgraph(g, district_label):
    relevant_nodes = get_district_nodes(g, district_label)
    return g.subgraph(relevant_nodes) 

def recombination_of_districts(g, all_districts):
    # Randomly sample a district
    print(len(all_districts))
    d1 = str(random.randint(1, len(all_districts)))
    d2 = find_neighboring_district(d1)
    d1_nodes = get_district_nodes(g, d1)
    d2_nodes = get_district_nodes(g, d2)
    combined_subgraph = nx.Graph(g.subgraph(d1_nodes + d2_nodes))
    cuttable = False
    count = 50
    print("Trying to find a cut")
    while cuttable is False: 
        # NOTE: Have to use PRIM's here becuase Kruskal's will return the same MST every time.
        mst_combined_subgraph =  nx.minimum_spanning_tree(combined_subgraph, algorithm="prim")
        drawGraph(mst_combined_subgraph)
        for (tail, head) in mst_combined_subgraph.edges: 
            mst_combined_subgraph.remove_edge(tail, head)
            print("tail, head")
            print(tail, head)
            components = nx.connected_components(mst_combined_subgraph)
            print(list(components))
            if (count == 0):
                cuttable = True 
                return
            else: 
                count -= 1
                mst_combined_subgraph.add_edge(tail, head)
            # TODO: Figure out edge cut algo

# ReCom Algo: 
# - Select one district
# - Select one of its neighboring districts 
# - Look at the subgraph induced by the vertices in both districts 
# - Make an MST for the graph 
# - For all edges in the MST 
#     - Does cutting this edges create two components with similar population sizes 
#         (for subcomponents created by the edge cut, calculat the total population and compare with a delta)
#     - YES: 
#         Done - keep cut
#     - NO: 
#         - continue iterating through edges 
# - Redistrict along that edge cut


def drawGraph(G): 
    options = {
        'node_color': 'blue',
        'node_size': 100,
        "with_labels":True,
        'width': 3,
        "font_weight": "bold"
    }
    plt.subplot(222)

    # Draw the graph we've been provided
    nx.draw_networkx(G, **options)
    plt.show()

g = import_graph(path_adjlist, path_metadata)
# drawGraph(g)

# For all districts, draw the graph
all_districts = ["1","2"]

for d_label in all_districts: 
    d = get_district_subgraph(g, d_label)
    eg = efficiency_gap(d)
    print(eg)

print("Recomb")
print("==========")
recombination_of_districts(g, all_districts)