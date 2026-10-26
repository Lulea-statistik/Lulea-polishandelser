#!/usr/bin/env python3
"""Read-only classification of repeated versus distinct road mentions."""
import unicodedata

def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())

def distinct_mentions(mentions, pilot_road):
    baseline = normalize(pilot_road)
    return [x.strip() for x in str(mentions or "").split("|")
            if x.strip() and normalize(x) != baseline]

def has_distinct_road(mentions, pilot_road):
    return bool(distinct_mentions(mentions, pilot_road))
