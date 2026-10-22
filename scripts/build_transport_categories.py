#!/usr/bin/env python3
"""Exploratory transport taxonomy; never overwrites the police's event type or geography."""
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from build_lulea_districts import district, UNKNOWN

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/events.csv"
OUT = ROOT / "docs/data/lulea_transport_monthly.csv"
AUDIT = ROOT / "data/audit_lulea_transport_candidates.csv"

def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(c for c in value if not unicodedata.combining(c))

def match(text, terms):
    return any(re.search(r"(?<![a-z])" + p + r"(?![a-z])", text) for p in terms)

MODES = {
    "Vägtrafik": [r"trafikolyck\w*", r"trafikbrott\w*", r"rattfylleri\w*", r"bilist\w*", r"personbil\w*", r"motorcykel\w*", r"lastbil\w*", r"vagtrafik\w*", r"fordonskontroll\w*"],
    "Kollektivtrafik": [r"buss\w*", r"busshallplats\w*", r"busstation\w*", r"kollektivtrafik\w*"],
    "Järnväg": [r"jarnvag\w*", r"tagolyck\w*", r"tagtrafik\w*", r"sparomrad\w*", r"lokforar\w*"],
    "Sjöfart": [r"batolyck\w*", r"fartyg\w*", r"sjotrafik\w*", r"batforar\w*", r"farja\w*"],
    "Flygtrafik": [r"flygplan\w*", r"flygtrafik\w*", r"flygplats\w*", r"helikopter\w*"],
    "Godstransporter": [r"lastbil\w*", r"godstransport\w*", r"farligt gods", r"transportfordon\w*"],
    "Gång- och cykeltrafik": [r"cykelolyck\w*", r"cyklist\w*", r"elsparkcykel\w*", r"fotgangar\w*", r"gangtrafik\w*"],
}
EVENT_KINDS = {
    "Olycka": [r"olyck\w*", r"kollision\w*", r"pakord\w*", r"avkorning\w*"],
    "Trafikbrott": [r"rattfylleri\w*", r"trafikbrott\w*", r"olovlig korning", r"fortkorning\w*"],
    "Kontroll": [r"kontroll\w*", r"nykterhetskontroll\w*"],
    "Brand": [r"brand\w*"],
    "Störning/säkerhet": [r"storning\w*", r"stopp\w*", r"fara\w*"],
}
# References to transport as a consequence of an unrelated incident are not mode evidence.
INCIDENT_CONTEXT = [r"forts till sjukhus", r"fordes till sjukhus", r"transporterades till sjukhus", r"ambulans till sjukhus"]
# These are precision classes, not new administrative districts.
LONG_ROAD = re.compile(r"(?<![a-z0-9])(?:e ?4|e ?10|vag(?:en)? ?(?:97|94|968|596))(?![0-9])")
JUNCTION = re.compile(r"(?<![a-z])(?:rondell\\w*|cirkulationsplats\\w*|korsning\\w*|trafikplats\\w*)(?![a-z])")
def transport_location_precision(row, transport_modes):
    if not transport_modes:
        return "Ej transport"
    place = norm(" ".join(str(row.get(k) or "") for k in ("title_location", "location_string", "headline")))
    if JUNCTION.search(place):
        return "Avgränsad trafikplats – verifiera"
    if LONG_ROAD.search(place):
        return "Lång vägsträcka – oprecis"
    if district(row) == UNKNOWN:
        return "Plats ej fastställd"
    return "Områdesanknuten – ej punktverifierad"

rows = []
unique = set()
# Verified same-incident publication pair: 107414 contains the subsequent update.
REPLACED_PUBLICATIONS = {"107404": "107414"}
aggregated = defaultdict(int)
for row in csv.DictReader(SOURCE.open(encoding="utf-8-sig", newline="")):
    if (row.get("geography_group") or "").strip() != "Luleå kommun":
        continue
    eid = (row.get("event_id") or "").strip()
    if eid in REPLACED_PUBLICATIONS:
        continue
    if eid and eid in unique:
        continue
    if eid:
        unique.add(eid)
    year, month = (row.get("year") or "").strip(), (row.get("month") or "").strip()
    if not (year.isdigit() and month.isdigit() and 1 <= int(month) <= 12):
        continue
    headline = norm(row.get("headline"))
    title = norm(row.get("title_location"))
    typ = norm(row.get("type_original"))
    narrative = norm(" ".join(str(row.get(k) or "") for k in ("description", "content")))
    primary = " ".join((headline, typ))
    secondary = " ".join((title, narrative))
    strong = [mode for mode, patterns in MODES.items() if match(primary, patterns)]
    contextual = [mode for mode, patterns in MODES.items() if match(secondary, patterns)]
    modes = sorted(set(strong + contextual))
    kinds = sorted(kind for kind, pats in EVENT_KINDS.items() if match(primary, pats))
    if not modes:
        continue
    relation = "Högre träffsäkerhet" if strong else "Kontextträff – kontroll krävs"
    if len(modes) > 1:
        relation = "Överlappande trafikslag – kontroll krävs"
    if not strong and match(narrative, INCIDENT_CONTEXT):
        relation = "Transport till vård omnämns – kontroll krävs"
    if "Flygtrafik" in modes and match(primary, [r"flygplats\\w*"]) and not match(primary, [r"flygplan\\w*", r"flygtrafik\\w*"]):
        relation = "Flygplats kan vara enbart platsangivelse – kontroll krävs"
    if "Sjöfart" in modes and not strong:
        relation = "Sjöfart endast i löptext – kontroll krävs"
    kind = kinds[0] if len(kinds) == 1 else ("Flera händelsetyper" if kinds else "Annan/oklar")
    geo = district(row)
    precision = transport_location_precision(row, modes)
    display_geography = "Vägsträcka – område ej fastställt" if precision == "Lång vägsträcka – oprecis" else geo
    rows.append({
        "event_id": eid, "year": year, "month": month.zfill(2),
        "geography_group": geo, "display_geography": display_geography,
        "location_precision": precision,
        "type_original": row.get("type_original") or "",
        "headline": (row.get("headline") or "")[:250],
        "modes": " | ".join(modes), "event_kind": kind,
        "review_status": relation, "candidate_sources": "rubrik/typ" if strong else "plats/beskrivning",
        "verified": "Nej",
    })
    # Multiple modes can refer to one event. Count distinct events per mode.
    for mode in modes:
        aggregated[(year, month.zfill(2), display_geography, precision, mode, kind, relation)] += 1

AUDIT.parent.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
fields = ["event_id", "year", "month", "geography_group", "display_geography", "location_precision", "type_original", "headline", "modes", "event_kind", "review_status", "candidate_sources", "verified"]
with AUDIT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["year", "month", "geography_group", "location_precision", "transport_mode", "event_kind", "review_status", "event_count"])
    for key, n in sorted(aggregated.items()):
        writer.writerow([*key, n])
print("Deduplicerade uppdateringspubliceringar:", REPLACED_PUBLICATIONS)
print("Transportkandidater:", len(rows), "unika händelser")
print("Platsnoggrannhet:", dict(Counter(r["location_precision"] for r in rows)))
print("Trafikslag:", dict(Counter(mode for r in rows for mode in r["modes"].split(" | "))))
print("Transportkandidater med Okänt delområde:", sum(r["geography_group"] == UNKNOWN for r in rows))
print("Okänt delområde per trafikslag:", dict(Counter(mode for r in rows if r["geography_group"] == UNKNOWN for mode in r["modes"].split(" | "))))
print("Andel okänd geografi bland transportkandidater:", round(100 * sum(r["geography_group"] == UNKNOWN for r in rows) / max(len(rows), 1), 1), "%")
print("Granskningsstatus:", dict(Counter(r["review_status"] for r in rows)))
print("Obs: trafikslag överlappar; summera inte olika trafikslag till antal unika händelser")
assert len(rows) == len({r["event_id"] for r in rows}), "Dubblerade händelser"
