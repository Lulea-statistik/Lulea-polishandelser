#!/usr/bin/env python3
"""Conservative evidence triage for priority road incidents; never publishes geographies."""
import csv, json, re
from collections import Counter
from pathlib import Path
from road_mentions_qa import distinct_mentions
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/"data/audit_lulea_road_priority_original_evidence.csv"
with src.open(encoding="utf-8",newline="") as f: rows=list(csv.DictReader(f))
if not rows:raise ValueError("No priority events to audit")
out=[]
for row in rows:
 road=row["pilot_road"].casefold().strip()
 place=(row.get("original_place_field") or "").strip()
 audit_place=(row.get("audit_place_field") or "").strip()
 narrative=(row.get("original_narrative") or "").strip()
 other=(row.get("other_road_mentions") or "").strip()
 distinct=distinct_mentions(other,road)
 place_l=place.casefold()
 if not place:
  status="saknat_originalplatsfält"
  reason="Originalets platsfält saknas"
 elif distinct:
  status="flera_vaguppgifter"
  reason="Ytterligare vägnamn i beskrivningen; kontrollera motsägelser"
 elif road not in place_l:
  status="vägnamn_saknas_i_originalplatsfält"
  reason="Pilotvägen kan inte bekräftas i ursprungligt platsfält"
 elif re.search(r"\b\d{1,4}\s*[a-z]?\b",place_l):
  status="möjlig_adress_eller_vägnummer"
  reason="Siffra i platsfält; kan vara adress eller vägnummer, kräver kontroll"
 elif re.search(r"\b(?:korsning(?:en)?|rondell(?:en)?|avfart(?:en)?|mellan|intill|nära|vid)\b",place_l):
  status="möjlig_precisering"
  reason="Relation till plats kan finnas, men saknar verifierade koordinater"
 else:
  status="enbart_väg_ledtråd"
  reason="Ingen ytterligare verifierbar position i ursprungligt platsfält"
 if road=="väderleden":
  reason+="; Väderledens vägklass är känslig för tröskelvärden"
 out.append({**row,"distinct_other_mentions":" | ".join(distinct),
   "evidence_class":status,"evidence_explanation":reason,
   "original_place_matches_pilot_road":"Ja" if road in place_l else "Nej",
   "narrative_available":"Ja" if narrative else "Nej",
   "geographical_decision":"Ej styrkt – oförändrad geografi",
   "manual_check":"Ja","publish":"NEJ"})
out.sort(key=lambda z:(z["priority"],z["pilot_road"],z["event_id"]))
if len({x["event_id"] for x in out})!=len(out):raise ValueError("Duplicate event IDs")
dest=ROOT/"data/audit_lulea_road_priority_evidence_triage.csv"
with dest.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print("ROAD_EVIDENCE_TRIAGE",json.dumps({"total":len(out),"by_class":dict(Counter(x["evidence_class"] for x in out)),"by_road":dict(Counter(x["pilot_road"] for x in out)),"by_priority":dict(Counter(x["priority"] for x in out))},ensure_ascii=False))
print("NO_PUBLICATION: No event location adjudicated")
