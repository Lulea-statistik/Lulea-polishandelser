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
    "bjurstrask", "sunderby sjukhus", "sunderbyns sjukhus", "sjukhuset", "sjukhus", "shell", "musikomat", "postnord"
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
        "orarna", "kyrkbyn", "bjurstrask", "sunderby sjukhus", "sunderbyns sjukhus", "sjukhuset", "sjukhus"},
    "verksamhet": {"shell", "musikomat", "postnord"},
    "vag_eller_bro": {"vagen", "gatan", "grand", "stigen", "leden", "bron"},
}
HOSPITAL_WORDS = re.compile(r"(?<![a-z])(?:sunderby sjukhus|sunderbyns sjukhus|sjukhuset|sjukhus)(?![a-z])")
HOSPITAL_TRANSPORT = re.compile(r"(?<![a-z])(?:fordes|fors|transporteras|transporterades|kordes|foras|hamtades|skjutsades|togs|akuttransport|ambulans).*?(?:till|pa) (?:sunderby |sunderbyns )?sjukhus(?:et)?(?![a-z])")
HOSPITAL_AT_SCENE = re.compile(r"(?<![a-z])(?:vid|pa|inne pa|utanfor|intill|i anslutning till) (?:sunderby |sunderbyns )?sjukhus(?:et)?(?![a-z])")
def hospital_context(event):
    fields = ("title_location", "location_string", "headline", "description", "content")
    excerpts = []
    tags = set()
    for field in fields:
        raw = normalize(event.get(field) or "")
        for m in HOSPITAL_WORDS.finditer(raw):
            snippet = raw[max(0, m.start()-110):min(len(raw), m.end()+75)]
            excerpts.append((field, snippet))
            if HOSPITAL_TRANSPORT.search(snippet):
                tags.add("transport_eller_vard")
            if HOSPITAL_AT_SCENE.search(snippet):
                tags.add("mojlig_handeleseplats")
    if not excerpts:
        return "", ""
    status = "Blandade signaler" if len(tags) > 1 else ("Möjlig händelseplats" if "mojlig_handeleseplats" in tags else ("Transport/vård – ej händelseplats" if "transport_eller_vard" in tags else "Oklart omnämnande"))
    return status, " | ".join(field + ": " + snippet for field, snippet in excerpts[:3])

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
        canonical_settlements = sorted(set("sunderbyn" if term in {"sunderby sjukhus", "sunderbyns sjukhus", "sjukhuset", "sjukhus"} else term for term in settlement_terms))
        settlement_review = (
            "Kontrollera ortens kommuntillhörighet, områdesindelning och händelseplats"
            if settlement_terms else ""
        )
        review_flags = []
        if len(canonical_settlements) > 1:
            review_flags.append("Flera ortnamn – kontrollera vilken plats som avser händelsen")
        if "kallax" in settlement_terms:
            review_flags.append("Kallax kan avse by, flygplats eller större område")
        # Sunderby sjukhus och orten Sunderbyn tillhör samma analysområde.
        # Enbart omnämnande av sjukhuset styr dock inte händelseplatsen.
        if any(term in matched for term in {"sjukhus", "sjukhuset"}):
            review_flags.append("Generiskt sjukhusord: lokal Sunderbyn-ledtråd, men verifiera att händelsen inträffade på sjukhuset")
        if "sunderbyn" in canonical_settlements and len(canonical_settlements) > 1:
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
        suggested_area = "Sunderbyn (lokal platsledtråd, händelserelation ej verifierad)" if canonical_settlements == ["sunderbyn"] else ("Rutvik (områdesgräns ej verifierad)" if canonical_settlements == ["rutvik"] else "")
        hospital_relation, hospital_excerpts = hospital_context(event)
        if hospital_relation == "Möjlig händelseplats":
            review_flags.append("Sjukhus som möjlig händelseplats: kontrollera originaltext innan beslut")
        elif hospital_relation == "Transport/vård – ej händelseplats":
            review_flags.append("Sjukhus omnämns i transport/vård-kontext: får inte ensamt styra områdesklassning")
        elif hospital_relation == "Oklart omnämnande":
            review_flags.append("Sjukhusomnämnande utan tydlig händelserelation")
        priority = "Flera källfält" if field_count >= 2 else ("Platsfält" if source_matches["title_location"] or source_matches["location_string"] else "Endast rubrik")
        rows.append({
            "event_id": eid, "year": event.get("year", ""),
            "title_location": title, "location_string": loc,
            "headline": headline[:250],
            "candidate_sources": " | ".join(field for field, terms in source_matches.items() if terms),
            "matched_terms": " | ".join(matched),
            "candidate_categories": " | ".join(categories),
            "settlement_terms": " | ".join(settlement_terms),
            "canonical_settlements": " | ".join(canonical_settlements),
            "settlement_review": settlement_review,
            "candidate_area": suggested_area,
            "hospital_relation": hospital_relation,
            "hospital_evidence": hospital_excerpts,
            "hospital_review_action": ("Granska som möjlig händelseplats" if hospital_relation == "Möjlig händelseplats" else ("Uteslut sjukhus som ensam platsgrund" if hospital_relation == "Transport/vård – ej händelseplats" else ("Kontrollera ursprunglig händelsetext" if hospital_relation else ""))),
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
        "candidate_sources","matched_terms","candidate_categories","settlement_terms","canonical_settlements","settlement_review","candidate_area","hospital_relation","hospital_evidence","hospital_review_action","review_flags","needs_geographic_verification","review_priority","evidence_relation","review_decision","verified_district","verification_source","reviewer_note","existing_group","proposed_group","review_status","review_note"])
    w.writeheader()
    w.writerows(rows)
print("Unknown Lulea placefield review rows:", len(rows))
print("Unique event IDs:", len({r["event_id"] for r in rows}))
from collections import Counter
print("Review groups:", dict(sorted(Counter(r["review_priority"] for r in rows).items())))
print("Settlement mentions (not approved districts):", dict(sorted(Counter(term for r in rows for term in r["settlement_terms"].split(" | ") if term).items(), key=lambda p: (-p[1], p[0]))))
print("Events requiring special review:", sum(bool(r["review_flags"]) for r in rows))
print("Hospital potential scene candidate IDs:", [r["event_id"] for r in rows if r["hospital_relation"] == "Möjlig händelseplats"])
print("Hospital context categories:", dict(sorted(Counter(r["hospital_relation"] for r in rows if r["hospital_relation"]).items())))
print("Candidate categories:", dict(sorted(Counter(category for r in rows for category in r["candidate_categories"].split(" | ")).items())))
assert len(rows) == len({r["event_id"] for r in rows}), "Duplicate event IDs in candidate review"
assert all(not r["proposed_group"] and not r["verified_district"] for r in rows), "Review must not invent classification"
