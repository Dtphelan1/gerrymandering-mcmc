# gerrymandering-mcmc
Markov chain monte carlo simulator used to assess the outliership of a district plan


## Rough Sketch of the Plan

The simulation we're going for here is a basic approach outlined in some of the work by Moon Duchin and others. Core terms we want to understand: 
- Precinct: The smallest unit of people/land division we'll consider in our algorithm. One precint can have a voting history, a population with demographic information.
- District: A group of coniguious precincts. Each district has one representative. How the district decides which representative they will elect can differ from state to state, but to simplify we will assume that all use plurality voting, as is the overwhelming case.
- State: From the models perspective, a state with `n` many representatives is broken up into `n` many contiguous districts.  
- Gerrymandering: The intentional redrawing of district lines (we'll look at for census tracts) by one party to the benefit of that party - often to increase the likelihood of that parties re-election. 
- Packing: A gerrymandering strategy wherein a single district is packed with multiple precints that all have a likelihood of voting for the same party. Since plurality voting means all you need is the greatest number of votes compared to your competitors, a party is disadvantaged by having one district poll unnecessarily high. For example, if 1 district polls at 95% Party A/5% Party B while 4 neighboring districts poll at 45% Party A/55% Party B, then Party A might have done better if they weren't packed so tightly; they could have had all 5 districts poll at >55% Party A in a perfect world. 
- Cracking: A gerrymandering strategy wherein a single district that leans Party A is broken up across multiple other neighbooring districts to decrease the overall number of districts that lean Party A. 

What we want to do: 
- Model a state's precints as the dual-graph of the planar breakdown of districts.
- Model a state's districts as n-1 edge-cuts 


Steps: 
======
1. Get a single graph file reading in through CLI 
2. Get a single graph file reading in through CLI with districts separated (sub-graphs of interest)
3. Get a single graph file reading in through CLI with information about each precinct (population, voting history for past election) 
4. Generate a new graph by modifying the graph fed in by flipping the district of nodes on the periphery of districts
5. Generate a new graph by using the ReCom technique 
    - Find two neighboring districts
    - Merge them into a single district 
    - Draw an MST for that single district
    - An edge is identied that will separate the merged area into two equal-sized districts. 
    - Removing that edge determines the new plan.

Arguments:
==========
- Path to the file of the map of interest 
- (opt) epsilon value by which the population can vary from district to district
- (opt)


THoughts: 
=========

Loading data from file: 
- add_nodes_from([(node, attrdict), (n2, ad2), ...]): Use (node, attrdict) tuples to update attributes for specific nodes.

for every precint: 
- add population information
- add voting history information 
- add district infroamtion at the local level (?) (or do we want to load that in at the global level)

Question: How do we keep track of what 

Algo for getting all district

Store at the class level the neighboring relationship between districts?

ReCom Algo: 
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


Efficiency Gap Algo for a District: 
- Identify party that wins for the district
- Set aside memeory for wasted votes for both parties
- For all precincts in the district: 
    - Did your candidate win the plurality? 
        - YES: INC wasted votes if you voted 