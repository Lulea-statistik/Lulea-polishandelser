#!/usr/bin/env python3
"""Non-publishing, event-level preview of exclusive Lulea geography."""
import csv,re,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_lulea_districts import district,UNKNOWN
from build_lulea_districts_expanded import subevent_district
from build_expanded_monthly import admin_non_event,NO_NEW_EVENT_RE
ROOT=Path(__file__).resolve().parents[1]
def read(path):
 with (ROOT/path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
events=read("data/events.csv")
details=read("data/summary_details_dedup.csv")
parsed={str(r.get("parent_event_id","")).strip() for r in details}
def yes(x):return str(x or "").strip().lower() in ("true","1")
def valid(r):return r.get("geography_group")=="Luleå kommun" and str(r.get("year","")).isdigit() and str(r.get("month","")).isdigit() and 1<=int(r["month"])<=12
# Conservative: classification by event type, not incidental road mention.
ROAD_TYPES=re.compile(r"trafikolycka|trafikbrott|rattfylleri|trafikkontroll|olovlig körning|smitning",re.I)
ROAD_REFERENCES=[("E4",r"(?<!\w)e\s*4(?!\w)"),("Väg 97",r"\b(?:väg|vag)\s*97\b"),("Väg 94",r"\b(?:väg|vag)\s*94\b"),("Bodenvägen",r"\bbodenvägen\b")]
def classify(typ,place,geo):
 if not ROAD_TYPES.search(typ or ""):return geo,"plats"
 matches=[name for name,pattern in ROAD_REFERENCES if re.search(pattern,place or "",re.I)]
 if len(matches)>1:return "Övrig väg, okänd väg","väg-motstridigt"
 if matches:return matches[0],"väg-känd"
 return "Övrig väg, okänd väg","väg-okänd"
records=[];seen=set()
def add(row,identifier,typ,geo,place,origin):
 category,quality=classify(typ,place,geo)
 records.append({"event_id":identifier,"source":origin,"year":row["year"],"month":row["month"],"type_original":typ,"base_geography":geo,"unified_geography":category,"classification":quality})
for row in events:
 if not valid(row):continue
 eid=str(row.get("event_id") or "").strip()
 if eid in seen:continue
 seen.add(eid)
 if yes(row.get("is_summary")):
  if eid in parsed:continue
  if NO_NEW_EVENT_RE.search(" ".join(row.get(k,"") or "" for k in ("headline","description","content"))):continue
  typ="Sammanfattning, ej uppdelad"
 else:
  if admin_non_event(row):continue
  typ=row.get("type_original") or "Okänd händelsetyp"
 place=" ".join(row.get(k) or "" for k in ("title_location","location_string"))
 add(row,eid,typ,district(row),place,"original")
for n,row in enumerate(details):
 if not valid(row) or not yes(row.get("include_as_extra")):continue
 typ=row.get("event_type_extracted") or "Okänd händelsetyp"
 add(row,str(row.get("parent_event_id") or "")+"#"+str(n),typ,subevent_district(row),row.get("place_text") or "","underhändelse")
before=Counter(r["base_geography"] for r in records)
after=Counter(r["unified_geography"] for r in records)
assert len(records)==sum(before.values())==sum(after.values()),"Counts changed"
assert len(records)==9743,("Unexpected expanded total",len(records))
out=ROOT/"data/audit_lulea_unified_geography_preview.csv"
with out.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
print("Unified preview total:",len(records))
print("Original unknown:",before[UNKNOWN],"unified unknown:",after[UNKNOWN])
print("Road classifications:",{k:v for k,v in after.items() if k.startswith(("E4","Väg","Bodenvägen","Övrig väg"))})
print("Classification quality:",dict(Counter(r["classification"] for r in records)))
print("PREVIEW ONLY: no published data modified")
