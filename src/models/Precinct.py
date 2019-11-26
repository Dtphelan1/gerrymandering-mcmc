class Precinct():
    def __init__(self, voting_history, population): 
        self.voting_history = voting_history;
        self.population = population;
        pass;

    def party_proxy(self):
        return self.voting_history;

    def population_size(self):
        return self.population;