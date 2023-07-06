import json

with open("./test_data/artists.json", "r") as openfile:
    ARTISTS = json.load(openfile)

with open("./test_data/events.json", "r") as openfile:
    EVENTS = json.load(openfile)
