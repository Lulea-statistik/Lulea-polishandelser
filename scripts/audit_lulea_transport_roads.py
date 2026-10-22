#!/usr/bin/env python3
"""Audit mentions of E4, route 97 and Bodenvagen; no geographic reassignment."""
import csv
import re
from collections import Counter
from pathlib import Path
from build_transport_categories import norm, district, UNKNOWN

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "E4": re.compile(r"(?<![a-z0-9])(?:e[ -]?4|europavag(?:en)?[ -]?4)(?![0-9])"),
    "Väg 97": re.compile(r"(?<![a-z0-9])(?:vag(?:en)?[ -]?97|lansvag[ -]?97|lv[ -]?97)(?![0-9])"),
    "Bodenvägen": re.compile(r"(?<![a-z])bodenvag(?:en)?(?![a-z])"),
}
FIELDS = ["title_location", "location_string", "headline", "description", "content"]
out = ROOT / "data/audit_lulea_transport_roads.csv"
rows = []
seen = set()
for event in csv.DictReader((ROOT / "data/events.csv").open(encoding="utf-8-sig", newline="")):
    if (event.get("geography_group") or "").strip() != "Luleå kommun":
        continue
    eid = (event.get("event_id") or "").strip()
    if eid in seen:
        continue
    seen.add(eid)
    matches = {name: [field for field in FIELDS if pat.search(norm(event.get(field))) ] for name, pat in PATTERNS.items()}
    matched = [name for name, fields in matches.items() if fields]
    if not matched:
        continue
    # Distinct aliases in one report must never imply distinct events.
    precision = "Lång vägsträcka – oprecis"
    text = norm(" ".join(event.get(field) or "" for field in FIELDS[:3]))
    if re.search(r"(?<![a-z])(?:rondell\\w*|cirkulationsplats\\w*|trafikplats\\w*|korsning\\w*)(?![a-z])", text):
        precision = "Trafikplats omnämns – kontrollera om avgränsad"
    rows.append({
        "event_id": eid, "year": event.get("year", ""), "road_mentions": " | ".join(matched),
        "fields": " | ".join(sorted({field for fields in matches.values() for field in fields})),
        "e4": "Ja" if "E4" in matched else "",
        "road97": "Ja" if "Väg 97" in matched else "",
        "bodenvagen": "Ja" if "Bodenvägen" in matched else "",
        "geography_group": district(event), "location_precision": precision,
        "location_string": (event.get("location_string") or "")[:180],
        "headline": (event.get("headline") or "")[:240],
        "verification": "Ej verifierad",
    })
out.parent.mkdir(exist_ok=True, parents=True)
with out.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [
        "event_id", "year", "road_mentions", "fields", "e4", "road97", "bodenvagen",
        "geography_group", "location_precision", "location_string", "headline", "verification"])
    writer.writeheader()
    writer.writerows(rows)
print("Vägomnämnanden – unika händelser:", len(rows))
print("Per väg (överlapp tillåtet):", dict(Counter(name for r in rows for name in r["road_mentions"].split(" | "))))
print("Väg 97 och Bodenvägen i samma händelse:", sum(bool(r["road97"] and r["bodenvagen"]) for r in rows))
print("Vägomnämnanden med okänt delområde:", sum(r["geography_group"] == UNKNOWN for r in rows))
print("Precisionsgrupper:", dict(Counter(r["location_precision"] for r in rows)))
assert len(rows) == len({r["event_id"] for r in rows})
