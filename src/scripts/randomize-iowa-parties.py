import random
import json
import datetime

with open("../data/iowa.json") as f:
    iowa = json.load(f)
    for precinct_label in iowa:
        parties = ["D", "R"]
        random_party = random.choice(parties)
        iowa[precinct_label]["voting_history"] = random_party
    new_iowa = open("../data/iowa" + str(datetime.datetime.now()) + ".json", "w")
    json.dump(iowa, new_iowa)
