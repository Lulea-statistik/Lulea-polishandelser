"""Classify remaining road mentions without deciding an event's geography."""
from road_mentions_qa import normalize, distinct_mentions

DESCRIPTIONS = ("återvändsgata", "korsning", "rondell", "trafikplats", "gata", "väg")
DESCRIPTION_KEYS = frozenset(normalize(s) for s in DESCRIPTIONS)

def partition_mentions(other, candidate):
    mentions = distinct_mentions(other, candidate)
    description = [s for s in mentions if normalize(s) in DESCRIPTION_KEYS]
    different = [s for s in mentions if normalize(s) not in DESCRIPTION_KEYS]
    return different, description
