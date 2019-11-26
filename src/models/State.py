import networkx as nx

class State(): 
    def __init__(self, data):
        edges = nx.read_adjlist('edges.txt');
        self.graph = nx.Graph()
        self.graph.