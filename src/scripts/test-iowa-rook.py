from pathlib import Path
import json
import networkx as nx
import matplotlib.pyplot as plt

def drawGraph(G, pos=None, options=None):
    """
        Given a graph, plot and draw it with these default options, or with options
    """

    options = options if options != None else {
        'node_color': 'blue',
        "with_labels":False,
        'node_size': 10
    }
    plt.subplot(222)
    plt.figure(figsize=(8,6))

    # Draw the graph we've been provided
    nx.draw_networkx(G, pos=pos, **options)
    plt.show()

with open('./data/iowa-rook.json') as f:
    data = json.load(f)

graph = nx.readwrite.json_graph.adjacency_graph(data)
pos = nx.planar_layout(graph)
drawGraph(graph, pos=pos)
