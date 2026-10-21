#!/usr/bin/env python3
"""Review unresolved Lulea location fields without guessing district assignments."""
import csv
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lulea_districts import district, UNKNOWN, normalize

root = Path(__file__).resolve().parents[1]
source = root / "data/events.csv"
out = root / "data/audit_lulea_placefield_review.csv"
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
        if not title and not loc:
            continue
        combined = normalize(title + " " + loc)
        if all(word not in combined for word in (
            "vagen", "gatan", "grand", "stigen", "leden", "bron", "rutvik",
            "smedsbyn", "kallax", "bensbyn", "pers on", "person", "sinksundet",
            "borjelslandet", "balinge", "stromsund", "bjorsbyn", "jamt on",
            "niemisel", "sunderbyn", "gammelstan", "gammelstad", "orarna",
            "kyrkbyn", "bjurstrask", "shell", "musikomat", "postnord"
        )):
            continue
        rows.append({
            "event_id": eid, "year": event.get("year", ""),
            "title_location": title, "location_string": loc,
            "headline": (event.get("headline") or "")[:250],
            "existing_group": UNKNOWN, "proposed_group": "",
            "review_status": "Manuell geografisk kontroll krävs",
            "review_note": "Platsfält kan avse väg, by eller verksamhet; ingen automatisk placering",
        })
out.parent.mkdir(exist_ok=True)
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [
        "event_id","year","title_location","location_string","headline",
        "existing_group","proposed_group","review_status","review_note"])
    w.writeheader()
    w.writerows(rows)
print("Unknown Lulea placefield review rows:", len(rows))
print("Unique event IDs:", len({r["event_id"] for r in rows}))
