#!/usr/bin/env python3
"""Review unresolved Lulea location fields without guessing district assignments."""
import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lulea_districts import district, UNKNOWN, normalize

root = Path(__file__).resolve().parents[1]
source = root / "data/events.csv"
out = root / "data/audit_lulea_placefield_review.csv"
PLACE_TERMS = (
    "vagen", "gatan", "grand", "stigen", "leden", "bron", "rutvik",
    "smedsbyn", "kallax", "bensbyn", "sinksundet", "borjelslandet",
    "balinge", "stromsund", "bjorsbyn", "jamton", "niemisel",
    "sunderbyn", "gammelstan", "gammelstad", "orarna", "kyrkbyn",
    "bjurstrask", "shell", "musikomat", "postnord"
)
rows = []
seen = set()
with source.open(encoding="utf-8-sig", newline="") as f:
    for event in csv.DictReader(f):
        if (event.get("geography_group") or "").strip() != "Luleå kommun":
            continue
        eid = (event.get("event_id") or "").strip()
        if eid and eid in seen:
            continue
        if eid:
            seen.add(eid)
        if district(event) != UNKNOWN:
            continue
        title = (event.get("title_location") or "").strip()
        loc = (event.get("location_string") or "").strip()
        headline = (event.get("headline") or "").strip()
        if not title and not loc and not headline:
            continue
        combined = normalize(title + " " + loc + " " + headline)
        if not any(word in combined for word in PLACE_TERMS):
            continue
        rows.append({
            "event_id": eid, "year": event.get("year", ""),
            "title_location": title, "location_string": loc,
            "headline": headline[:250],
            "candidate_sources": " | ".join(field for field, value in (("title_location", title), ("location_string", loc), ("headline", headline)) if any(word in normalize(value) for word in PLACE_TERMS)),
            "existing_group": UNKNOWN, "proposed_group": "",
            "review_status": "Manuell geografisk kontroll krävs",
            "review_note": "Platsfält kan avse väg, by eller verksamhet; ingen automatisk placering",
        })
out.parent.mkdir(exist_ok=True)
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [
        "event_id","year","title_location","location_string","headline",
        "candidate_sources","existing_group","proposed_group","review_status","review_note"])
    w.writeheader()
    w.writerows(rows)
print("Unknown Lulea placefield review rows:", len(rows))
print("Unique event IDs:", len({r["event_id"] for r in rows}))
