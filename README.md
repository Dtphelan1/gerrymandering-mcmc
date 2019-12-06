# gerrymandering-mcmc
Markov chain monte carlo simulator used to assess the outliership of a district plan


## Setup
- This project was built using `python 3.7.5`, `pyenv` and `pyenv-virtualenv`
- To install all dependencies required, run `pip install -r requirements.txt`


## Usage
- `python cli.py -h` for more help


## Project Explained
This project (mirroring the work of the Metric Geometry and Gerrymandering Group) explores one way of quantifying the likelihood a district is gerrymandered. In particular, this project looks at Markov Chain Monte Carlo simulation as a way of exploring how districts would be redistricted by using a new method of district-generation called Recombination (ReCom)

Several important technical detials regarding this project include:
- We model a state graphically by looking at the dual-graph of that state's precincts. Since this is a planar graph to begin with, we know the dual will also be planar.
- For the scope of data created by this project, two precincts are adjacent if they are rook-adjacent; we will not be complicating matters with queen adjacency.
- Given a graph-file (supported is a custom format described in the **Data_Format** section below) build an ensemble of simulated redistrictings and plot relevant key statistics for those redistrictings
- Some of the key statistics we will be looking at are:
    - Efficiency Gap for a given district
    - Number of total winning precincts voting "D"
    - Number of total winning precincts voting "R"

#### Terms:
The simulation we're going for here is a basic approach outlined in some of the work by Moon Duchin and others. For references, see the **References** section below. Before starting any technical explanation, the following core terms need to be understood:
- Precinct: The smallest unit of people/land division we'll consider in our algorithm. One precint can have a voting history, a population with demographic information.
- District: A group of coniguious precincts. Each district has one representative. How the district decides which representative they will elect can differ from state to state, but to simplify we will assume that all use plurality voting, as is the overwhelming case.
- State: From the models perspective, a state with `n` many representatives is broken up into `n` many contiguous districts.
- Gerrymandering: The intentional redrawing of district lines (we'll look at for census tracts) by one party to the benefit of that party - often to increase the likelihood of that parties re-election.
- Packing: A gerrymandering strategy wherein a single district is packed with multiple precints that all have a likelihood of voting for the same party. Since plurality voting means all you need is the greatest number of votes compared to your competitors, a party is disadvantaged by having one district poll unnecessarily high. For example, if 1 district polls at 95% Party A/5% Party B while 4 neighboring districts poll at 45% Party A/55% Party B, then Party A might have done better if they weren't packed so tightly; they could have had all 5 districts poll at >55% Party A in a perfect world.
- Cracking: A gerrymandering strategy wherein a single district that leans Party A is broken up across multiple other neighbooring districts to decrease the overall number of districts that lean Party A.
- Wasted Votes: In a given district, wasted votes are a) votes cast for the losing party; b) extra votes beyond the minimum required to win for the winnning party


## Technical Roadmap:
1. Get a single graph file reading in through CLI
2. Get a single graph file reading in through CLI with districts separated (sub-graphs of interest)
3. Get a single graph file reading in through CLI with information about each precinct (population, voting history for past election)
4. Generate a new graph by modifying the graph fed in by flipping the district of nodes on the periphery of districts
5. Generate a new graph by using the ReCom technique
    - Find two neighboring districts
        - Do this by looking at the node-boundary for all nodes in a district
    - Merge them into a single district
    - Draw an Spanning Tree for that single district
    - For all edges in that Spanning Tree
        - Find an edge s.t. removing this edge produce a "valid" redistricting plan
    - Update the graph with our new districts

## More Psuedocode for the Curious:

#### Loading data from file:
Add_nodes_from([(node, attrdict), (n2, ad2), ...]): Use (node, attrdict) tuples to update attributes for specific nodes.
for every precint:
    - add population information
    - add voting history information
    - add district infroamtion at the local level (?) (or do we want to load that in at the global level)
Thought: Store at the class level the neighboring relationship between districts?

#### ReCom Algo:
- Select one district
- Select one of its neighboring districts
- Look at the subgraph induced by the vertices in both districts
- Make an MST for the graph
- For all edges in the MST
    - Does cutting this edges create two components with similar population sizes
        (for subcomponents created by the edge cut, calculat the total population and compare with a delta)
    - YES:
        Done - keep cut
    - NO:
        - continue iterating through edges
- Redistrict along that edge cut

#### Efficiency Gap Algo for a District:
- Calculate the amount of votes required for a party to win a district
- Identify party that wins for the district
- For all precincts in the district:
    - Determine the winning party
    - For the losing party:
        - All precincts voting in favor are wasted
    - For the winning party:
        - Wasted precinct votes are those that go beyond the amount required to win the district
- The efficiency gap for the district:
    - (losing_votes_wasted - winning_votes_wasted) / total_votes


## References:
- Metric Geometry and Gerrymandering Group:
    - Webpage: https://mggg.org/
    - Twitter: https://twitter.com/gerrymandr
    - GitHub: https://github.com/mggg
- "Recombination: A family of Markov chains for redistricting"; Daryl DeFord, Moon Duchin, and Justin Solomon
