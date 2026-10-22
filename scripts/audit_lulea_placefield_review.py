#!/usr/bin/env python3
"""Review unresolved Lulea location fields without guessing district assignments."""
import csv
import re
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
ROAD_SUFFIXES = {"vagen", "gatan", "grand", "stigen", "leden", "bron"}
TERM_PATTERNS = {term: re.compile((r"(?<![a-z])[a-z]{2,}" if term in ROAD_SUFFIXES else r"(?<![a-z])") + re.escape(term) + r"(?![a-z])") for term in PLACE_TERMS}
def detect(value):
    value = normalize(value)
    return [term for term, pattern in TERM_PATTERNS.items() if pattern.search(value)]
PLACE_CATEGORIES = {
    "ort_eller_by": {"rutvik", "smedsbyn", "kallax", "bensbyn", "sinksundet",
        "borjelslandet", "balinge", "stromsund", "bjorsbyn", "jamton",
        "niemisel", "sunderbyn", "gammelstan", "gammelstad",
        "orarna", "kyrkbyn", "bjurstrask"},
    "verksamhet": {"shell", "musikomat", "postnord"},
    "vag_eller_bro": {"vagen", "gatan", "grand", "stigen", "leden", "bron"},
}
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
        if not detect(combined):
            continue
        source_matches = {field: detect(value) for field, value in (("title_location", title), ("location_string", loc), ("headline", headline))}
        matched = sorted(set(term for terms in source_matches.values() for term in terms))
        field_count = sum(bool(terms) for terms in source_matches.values())
        categories = sorted(kind for kind, names in PLACE_CATEGORIES.items() if any(term in names for term in matched))
        # Candidate only: don't infer official district from a place name.
        settlement_terms = sorted(set(matched) & PLACE_CATEGORIES["ort_eller_by"])
        settlement_review = (
            "Kontrollera ortens kommuntillhörighet, områdesindelning och händelseplats"
            if settlement_terms else ""
        )
        review_flags = []
        if len(settlement_terms) > 1:
            review_flags.append("Flera ortnamn – kontrollera vilken plats som avser händelsen")
        if "kallax" in settlement_terms:
            review_flags.append("Kallax kan avse by, flygplats eller större område")
        # Sunderby sjukhus och orten Sunderbyn tillhör samma analysområde.
        # Enbart omnämnande av sjukhuset styr dock inte händelseplatsen.
        if "sunderbyn" in settlement_terms and len(settlement_terms) > 1:
            review_flags.append("Sunderbyn tillsammans med annan ort: verifiera händelseplats")
        if "rutvik" in settlement_terms and any(term in matched for term in ROAD_SUFFIXES):
            review_flags.append("Rutviks större område kan omfatta vägen: kontrollera händelseplats och områdesgräns")
        if set(settlement_terms) & {"kyrkbyn", "gammelstan", "gammelstad"}:
            review_flags.append("Gammelstad/Kyrkbyn – verifiera platsens innebörd")
        if any(term in matched for term in ROAD_SUFFIXES):
            review_flags.append("Väg eller bro kan sträcka sig över flera områden")
        if "verksamhet" in categories:
            review_flags.append("Verksamhetens läge och händelserelation måste verifieras")
        if settlement_terms and not (source_matches["title_location"] or source_matches["location_string"]):
            review_flags.append("Ortnamn endast i rubrik")
        suggested_area = "Sunderbyn" if settlement_terms == ["sunderbyn"] else ("Rutvik (områdesgräns ej verifierad)" if settlement_terms == ["rutvik"] else "")
        priority = "Flera källfält" if field_count >= 2 else ("Platsfält" if source_matches["title_location"] or source_matches["location_string"] else "Endast rubrik")
        rows.append({
            "event_id": eid, "year": event.get("year", ""),
            "title_location": title, "location_string": loc,
            "headline": headline[:250],
            "candidate_sources": " | ".join(field for field, terms in source_matches.items() if terms),
            "matched_terms": " | ".join(matched),
            "candidate_categories": " | ".join(categories),
            "settlement_terms": " | ".join(settlement_terms),
            "settlement_review": settlement_review,
            "candidate_area": suggested_area,
            "review_flags": " | ".join(review_flags),
            "needs_geographic_verification": "Ja",
            "review_priority": priority,
            "evidence_relation": "Ej granskad: platsen kan avse händelse, färdväg eller omnämnande",
            "review_decision": "",
            "verified_district": "",
            "verification_source": "",
            "reviewer_note": "",
            "existing_group": UNKNOWN, "proposed_group": "",
            "review_status": "Manuell geografisk kontroll krävs",
            "review_note": "Platsfält kan avse väg, by eller verksamhet; ingen automatisk placering",
        })
out.parent.mkdir(exist_ok=True)
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [
        "event_id","year","title_location","location_string","headline",
        "candidate_sources","matched_terms","candidate_categories","settlement_terms","settlement_review","candidate_area","review_flags","needs_geographic_verification","review_priority","evidence_relation","review_decision","verified_district","verification_source","reviewer_note","existing_group","proposed_group","review_status","review_note"])
    w.writeheader()
    w.writerows(rows)
print("Unknown Lulea placefield review rows:", len(rows))
print("Unique event IDs:", len({r["event_id"] for r in rows}))
from collections import Counter
print("Review groups:", dict(sorted(Counter(r["review_priority"] for r in rows).items())))
print("Settlement mentions (not approved districts):", dict(sorted(Counter(term for r in rows for term in r["settlement_terms"].split(" | ") if term).items(), key=lambda p: (-p[1], p[0]))))
print("Events requiring special review:", sum(bool(r["review_flags"]) for r in rows))
print("Candidate categories:", dict(sorted(Counter(category for r in rows for category in r["candidate_categories"].split(" | ")).items())))
assert len(rows) == len({r["event_id"] for r in rows}), "Duplicate event IDs in candidate review"
assert all(not r["proposed_group"] and not r["verified_district"] for r in rows), "Review must not invent classification"
