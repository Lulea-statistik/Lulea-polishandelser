#!/usr/bin/env python3
"""Shared conservative publication deduplication for event analytics.

Retain every police source record. Only explicitly reviewed event IDs are
collapsed in analytical counts. Suspected duplicates must be audited first.
"""
from collections import defaultdict
from difflib import SequenceMatcher
import re
import unicodedata

# 2019-02-14: same taxi/car crash at Gammelstadsvagen/Bodenvagen.
# 107414 is the updated notice; 107404 is its earlier version.
REPLACED_BY = {"107404": "107414"}

# Distinct incidents despite generic or near-identical police headlines.
# A negative review decision is not an automatic positive dedup decision.
DO_NOT_MERGE = [
    {"243612", "243613"},  # Innerstaden woman vs Skutviken man
    {"251321", "251346"},  # differing people and offences
    {"257284", "257299"},  # teenager vs adult man
]

def prohibited_merge(a, b):
    return any({str(a), str(b)} <= group for group in DO_NOT_MERGE)


def validate_decisions():
    for old, current in REPLACED_BY.items():
        assert old != current, "A publication cannot supersede itself"
        assert current not in REPLACED_BY, "Canonical version must not be superseded"
        assert not prohibited_merge(old, current), "Protected separate events must never be merged"

def canonical_event_id(event_id):
    key = str(event_id or "").strip()
    return REPLACED_BY.get(key, key)

def is_superseded(row):
    return str(row.get("event_id") or "").strip() in REPLACED_BY

def normalized(text):
    t = unicodedata.normalize("NFKD", str(text or "").casefold())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()

def candidate_pairs(rows):
    """Identify possible same-day republications; never silently merge them."""
    buckets = defaultdict(list)
    for row in rows:
        eid = str(row.get("event_id") or "").strip()
        if not eid:
            continue
        day = str(row.get("date") or "").strip() or str(row.get("year") or "") + "-" + str(row.get("month") or "")
        headline = normalized(row.get("headline") or row.get("description"))
        if not headline:
            continue
        buckets[(day, normalized(row.get("type_original")))].append((eid, headline, row))
    for (day, typ), group in buckets.items():
        # Restrict pairwise comparisons to identical leading headline signature.
        subgroups = defaultdict(list)
        for eid, headline, row in group:
            subgroups[headline[:70]].append((eid, headline, row))
        for subset in subgroups.values():
            if len(subset) < 2:
                continue
            for i in range(len(subset)):
                for j in range(i+1,len(subset)):
                    a, b = subset[i], subset[j]
                    if a[0] == b[0]:
                        continue
                    pa, pb = normalized(a[2].get("location_string")), normalized(b[2].get("location_string"))
                    if pa and pb and pa != pb:
                        continue
                    similarity = SequenceMatcher(None,a[1],b[1]).ratio()
                    if similarity < .97:
                        continue
                    yield {"date":day,"type_original":typ,"event_id_a":a[0],"event_id_b":b[0],
                           "headline_similarity":round(similarity,3),
                           "a_shorter_content":len(normalized(a[2].get("content")))<len(normalized(b[2].get("content"))),
                           "review_status":"Möjlig uppdatering – manuellt beslut krävs"}

validate_decisions()
