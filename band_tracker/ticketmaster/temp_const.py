import json

with open("./band_tracker/ticketmaster/artists.json", "r") as openfile:
    ARTISTS = json.load(openfile)

with open("./band_tracker/ticketmaster/events.json", "r") as openfile:
    EVENTS = json.load(openfile)

with open("./band_tracker/ticketmaster/events_of_sample.json", "r") as openfile:
    EVENTS_OF_SAMPLE = json.load(openfile)
