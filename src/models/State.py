from pathlib import Path
import json
import random
import networkx as nx
from networkx.algorithms import tree
import matplotlib.pyplot as plt
from functools import reduce

class State():
    def __init__(self, path_graph):
