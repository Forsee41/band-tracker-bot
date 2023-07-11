import json

with open("./test_data/artists.json", "r") as openfile:
    ARTISTS = json.load(openfile)

with open("./test_data/events.json", "r") as openfile:
    EVENTS = json.load(openfile)

with open("./test_data/artists(small).json", "r") as openfile:
    ARTISTS_SMALL = json.load(openfile)

with open("./test_data/events(small).json", "r") as openfile:
    EVENTS_SMALL = json.load(openfile)
