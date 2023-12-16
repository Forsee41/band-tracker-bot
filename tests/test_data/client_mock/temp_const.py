import json

with open("tests/test_data/client_mock/artists.json", "r") as openfile:
    ARTISTS = json.load(openfile)

with open("tests/test_data/client_mock/events.json", "r") as openfile:
    EVENTS = json.load(openfile)

with open("tests/test_data/client_mock/artists(small).json", "r") as openfile:
    ARTISTS_SMALL = json.load(openfile)

with open("tests/test_data/client_mock/events(small).json", "r") as openfile:
    EVENTS_SMALL = json.load(openfile)
