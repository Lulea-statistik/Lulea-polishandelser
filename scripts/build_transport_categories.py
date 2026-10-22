#!/usr/bin/env python3
"""Exploratory transport taxonomy; never overwrites the police's event type or geography."""
import csv
from police_publication_dedup import is_superseded
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
JUNCTION = re.compile(r"(?<![a-z])(?:rondell\w*|cirkulationsplats\w*|korsning\w*|trafikplats\w*)(?![a-z])")

# Independent road reference; never infer a district from the road name.
ROAD_PATTERNS = [
    ("E4", r"(?<![a-z0-9])e ?4(?![0-9])"),
    ("E10", r"(?<![a-z0-9])e ?10(?![0-9])"),
    ("Väg 97", r"vag(?:en)? ?97(?![0-9])"),
    ("Väg 94", r"vag(?:en)? ?94(?![0-9])"),
    ("Bodenvägen", r"bodenvag(?:en)?"),
]
def road_reference(row):
    primary = norm(" ".join(str(row.get(k) or "") for k in ("title_location","location_string","headline")))
    for name, pattern in ROAD_PATTERNS:
        if re.search(pattern, primary):
            return name
    return "Väg ej angiven"


# Named junction references are candidates, not verified incident coordinates.
JUNCTION_NAMES = [
    ("Trafikplats Råneå södra", "trafikplats ranea sodra"),
    ("Trafikplats Gäddvik södra", "trafikplats gaddvik sodra"),
    ("Trafikplats Notviken", "trafikplats notviken"),
    ("Trafikplats Jämtön", "trafikplats jamton"),
    ("Trafikplats Gäddvik", "trafikplats gaddvik"),
    ("Trafikplats Antnäs", "trafikplats antnas"),
    ("Trafikplats Måttsund", "trafikplats mattsund"),
    ("Gammelstadsvägen/Bodenvägen", "gammelstadsvagen/bodenvagen"),
    ("Svartövägen/Bodenvägen", "svartovagen/bodenvagen"),
    ("Mjölkuddsvägen/väg 97", "mjolkuddsvagen/vag 97"),
    ("E4/väg 383", "e4/vag 383"),
]
def junction_reference(row):
    place = norm(" ".join(str(row.get(k) or "") for k in ("title_location","location_string","headline")))
    compact = re.sub(r"\s*/\s*", "/", place)
    for name, needle in JUNCTION_NAMES:
        if needle in compact:
            return name
    # Explicit street/street pairs in police headings; a reference, not a verified coordinate.
    explicit = re.search(r"(?:korsning(?:en)?\\s+|vid\\s+)([a-z0-9åäö-]+(?:vägen|gatan|leden))\\s*/\\s*([a-z0-9åäö-]+(?:vägen|gatan|leden))", place)
    if explicit:
        return explicit.group(1).capitalize() + "/" + explicit.group(2).capitalize()
    # Named interchanges with an explicit location marker, not a vague proximity phrase.
    if "trafikplats norra sunderbyn" in place:
        return "Trafikplats Norra Sunderbyn"
    return "Trafikplats ej angiven"

def bus_stop_reference(row):
    # Bus station is deliberately not classified as a bus stop.
    place = norm(" ".join(str(row.get(k) or "") for k in ("title_location", "location_string", "headline")))
    if "busstation" in place or "bussterminal" in place:
        return "Hållplats ej angiven"
    if re.search(r"busshallplats|hallplats", place):
        return "Busshållplats – namn ej verifierat"
    return "Hållplats ej angiven"

def transport_location_precision(row, transport_modes):
    if not transport_modes:
        return "Ej transport"
    place = norm(" ".join(str(row.get(k) or "") for k in ("title_location", "location_string", "headline")))
    # Merely mentioning a junction is not proof that the incident happened at it.
    if JUNCTION.search(place):
        return "Trafikplats omnämns – verifiera händelseplats"
    if LONG_ROAD.search(place):
        return "Lång vägsträcka – oprecis"
    if district(row) == UNKNOWN:
        return "Plats ej fastställd"
    return "Områdesanknuten – ej punktverifierad"

rows = []
unique = set()
# Verified same-incident publication pair: 107414 contains the subsequent update.
from police_publication_dedup import REPLACED_BY
REPLACED_PUBLICATIONS = REPLACED_BY
aggregated = defaultdict(int)
for row in csv.DictReader(SOURCE.open(encoding="utf-8-sig", newline="")):
    if (row.get("geography_group") or "").strip() != "Luleå kommun":
        continue
    eid = (row.get("event_id") or "").strip()
    if is_superseded(row):
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
    if "Flygtrafik" in modes and match(primary, [r"flygplats\w*"]) and not match(primary, [r"flygplan\w*", r"flygtrafik\w*"]):
        relation = "Flygplats kan vara enbart platsangivelse – kontroll krävs"
    if "Sjöfart" in modes and not strong:
        relation = "Sjöfart endast i löptext – kontroll krävs"
    kind = kinds[0] if len(kinds) == 1 else ("Flera händelsetyper" if kinds else "Annan/oklar")
    geo = district(row)
    precision = transport_location_precision(row, modes)
    road = road_reference(row)
    junction = junction_reference(row)
    bus_stop = bus_stop_reference(row) if "Kollektivtrafik" in modes else "Hållplats ej angiven"
    display_geography = "Vägsträcka – område ej fastställt" if precision == "Lång vägsträcka – oprecis" else geo
    rows.append({
        "event_id": eid, "year": year, "month": month.zfill(2),
        "geography_group": geo, "display_geography": display_geography,
        "location_precision": precision, "road_reference": road, "junction_reference": junction, "bus_stop_reference": bus_stop,
        "type_original": row.get("type_original") or "",
        "headline": (row.get("headline") or "")[:250],
        "modes": " | ".join(modes), "event_kind": kind,
        "review_status": relation, "candidate_sources": "rubrik/typ" if strong else "plats/beskrivning",
        "verified": "Nej",
    })
    # Multiple modes can refer to one event. Count distinct events per mode.
    for mode in modes:
        aggregated[(year, month.zfill(2), display_geography, precision, road, junction, bus_stop if mode == "Kollektivtrafik" else "Hållplats ej angiven", mode, kind, relation)] += 1

AUDIT.parent.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
fields = ["event_id", "year", "month", "geography_group", "display_geography", "location_precision", "road_reference", "junction_reference", "bus_stop_reference", "type_original", "headline", "modes", "event_kind", "review_status", "candidate_sources", "verified"]
with AUDIT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["year", "month", "geography_group", "location_precision", "road_reference", "junction_reference", "bus_stop_reference", "transport_mode", "event_kind", "review_status", "event_count"])
    for key, n in sorted(aggregated.items()):
        writer.writerow([*key, n])
print("Deduplicerade uppdateringspubliceringar:", REPLACED_PUBLICATIONS)
print("Transportkandidater:", len(rows), "unika händelser")
print("Platsnoggrannhet:", dict(Counter(r["location_precision"] for r in rows)))
print("Namngivna trafikplatsreferenser:", dict(Counter(r["junction_reference"] for r in rows if r["junction_reference"] != "Trafikplats ej angiven")))
# Audit coverage explicitly; the 51 broad junction mentions are not all named sites.
mentioned = [r for r in rows if r["location_precision"] == "Trafikplats omnämns – verifiera händelseplats"]
unnamed = [r for r in mentioned if r["junction_reference"] == "Trafikplats ej angiven"]
named = [r for r in rows if r["junction_reference"] != "Trafikplats ej angiven"]
print("Trafikplats QA: omnämnanden", len(mentioned), "namngivna inom omnämnanden", len(mentioned)-len(unnamed), "utan namngiven matchning", len(unnamed))
print("Trafikplats QA: namngivna oavsett precisionsklass", len(named))
for r in unnamed[:35]:
    print("UNNAMED_JUNCTION_REVIEW",r["event_id"],repr(r["headline"][:170]),repr(r["road_reference"]))
for r in named:
    print("NAMED_JUNCTION_REVIEW",r["event_id"],repr(r["junction_reference"]),repr(r["road_reference"]),repr(r["location_precision"]))
print("Trafikslag:", dict(Counter(mode for r in rows for mode in r["modes"].split(" | "))))
print("Transportkandidater med Okänt delområde:", sum(r["geography_group"] == UNKNOWN for r in rows))
print("Okänt delområde per trafikslag:", dict(Counter(mode for r in rows if r["geography_group"] == UNKNOWN for mode in r["modes"].split(" | "))))
print("Andel okänd geografi bland transportkandidater:", round(100 * sum(r["geography_group"] == UNKNOWN for r in rows) / max(len(rows), 1), 1), "%")
print("Granskningsstatus:", dict(Counter(r["review_status"] for r in rows)))
print("Obs: trafikslag överlappar; summera inte olika trafikslag till antal unika händelser")
assert len(rows) == len({r["event_id"] for r in rows}), "Dubblerade händelser"
