#!/usr/bin/env python3
"""Skapa expanderad stadsdelsserie utan att ärva sammanfattningens plats."""
import csv
from police_publication_dedup import is_superseded
from collections import defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_lulea_districts import district, UNKNOWN
from build_expanded_monthly import admin_non_event, NO_NEW_EVENT_RE
ROOT=Path(__file__).resolve().parents[1]
EVENTS=ROOT/"data/events.csv"
DETAILS=ROOT/"data/summary_details_dedup.csv"
OUT=ROOT/"docs/data/lulea_district_expanded_monthly.csv"
def yes(v):return str(v or "").strip().casefold() in ("true","1")
def is_lulea(r):return (r.get("geography_group") or "").strip()=="Luleå kommun"
def valid(r):return str(r.get("year","")).isdigit() and str(r.get("month","")).isdigit() and 1<=int(r["month"])<=12
def key(r,typ,geo):return (str(r["year"]),f'{int(r["month"]):02d}',geo,typ)
with EVENTS.open(encoding="utf-8-sig",newline="") as f:
 events=list(csv.DictReader(f))
with DETAILS.open(encoding="utf-8-sig",newline="") as f:
 details=list(csv.DictReader(f))
parsed_ids={str(r.get("parent_event_id","")).strip() for r in details}
counts=defaultdict(int)
seen=set()
for row in events:
 if not is_lulea(row) or not valid(row) or is_superseded(row):continue
 eid=str(row.get("event_id","")).strip()
 if eid and eid in seen:continue
 if eid:seen.add(eid)
 if yes(row.get("is_summary")):
  if eid in parsed_ids:continue
  narrative=" ".join(row.get(k,"") or "" for k in ("headline","description","content"))
  if NO_NEW_EVENT_RE.search(narrative):continue
  typ="Sammanfattning, ej uppdelad"
 else:
  if admin_non_event(row):continue
  typ=row.get("type_original") or "Okänd händelsetyp"
 counts[key(row,typ,district(row))]+=1
for row in details:
 if not yes(row.get("include_as_extra")) or not is_lulea(row) or not valid(row):continue
 if str(row.get("parent_event_id") or "").strip() in ("107404",):continue
 # Plats från denna underhändelse, ALDRIG från föräldersammanfattningen.
 specific={"title_location":row.get("place_text") or "",
           "location_string":"","headline":"",
           "description":row.get("description") or "","content":""}
 geo=district(specific)
 counts[key(row,row.get("event_type_extracted") or "Okänd händelsetyp",geo)]+=1
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open("w",encoding="utf-8",newline="") as f:
 writer=csv.writer(f)
 writer.writerow(["year","month","geography_group","type_original","event_count"])
 for k,v in sorted(counts.items()):writer.writerow([*k,v])
print("Expanded Lulea district events:",sum(counts.values()),"unknown:",sum(v for k,v in counts.items() if k[2]==UNKNOWN))
