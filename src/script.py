from pathlib import Path
import json
import networkx as nx
import matplotlib.pyplot as plt

# Path to the relevant file we're testing 
path_adjlist = "./data/adjlist.txt"
path_metadata = "./data/precint-data.json"

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
    winning_votes_wasted = winning_votes - votes_to_win;
    losing_votes_wasted = losing_votes
    efficiency_gap = (losing_votes_wasted - winning_votes_wasted) / total_votes
    return (efficiency_gap, winning_group)

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
    nx.draw_spectral(G.subgraph(["d",'e','f','g','h']), **options)
    nx.draw_spectral(G.subgraph(["a", "b", "c"]), **options)
    # plt.show();

g = import_graph(path_adjlist, path_metadata)

def get_district(g, district_label):
    relevant_nodes = [n for n in g.nodes if g.nodes[n]["district"] is district_label]
    return g.subgraph(relevant_nodes) 

# drawGraph(g)
all_districts = ["1","2"]

for d_label in all_districts: 
    d = get_district(g, d_label)
    x = efficiency_gap(d)
    print(x)