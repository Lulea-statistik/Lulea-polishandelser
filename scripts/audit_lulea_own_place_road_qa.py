#!/usr/bin/env python3
"""QA of unique own-place road names among still-unknown road events; no publishing."""
import csv,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
# The discovery module exposes exactly the same candidate parsing rules.
from audit_lulea_unknown_road_names import records,events,details,ROAD_WORD,ROAD_NO,ALIASES
ROOT=Path(__file__).resolve().parents[1]
def names(text):
 a={ALIASES.get(x.casefold(),x.casefold()) for x in ROAD_WORD.findall(text or "") if x.casefold() not in ("riksväg","länsväg","landsväg")}
 a|={"Väg "+v for v in ROAD_NO.findall(text or "")}
 return a
items=[]; statuses=Counter(); byroad=Counter()
for row in records:
 if row["classification"]!="väg-okänd":continue
 eid=row["event_id"]
 if row["source"]=="underhändelse":
  try:d=details[int(eid.rsplit("#",1)[1])]
  except (ValueError,IndexError):continue
  place=d.get("place_text") or "";description=d.get("description") or ""
 else:
  d=events.get(eid,{})
  place=" ".join(d.get(k) or "" for k in ("title_location","location_string"))
  description=" ".join(d.get(k) or "" for k in ("headline","description"))
 primary=names(place)
 if not primary:continue
 other=names(description)
 # Exact one own-field road, with no conflicting road explicitly mentioned elsewhere.
 status="Entydig vägledtråd – manuell kontroll"
 if len(primary)>1:status="Flera vägar i eget platsfält – manuell kontroll"
 elif other-primary:status="Motstridande eller ytterligare vägomnämnande – manuell kontroll"
 name=next(iter(primary)) if len(primary)==1 else "Flera vägar"
 statuses[status]+=1
 if len(primary)==1:byroad[name]+=1
 items.append({"event_id":eid,"source":row["source"],"year":row["year"],"month":row["month"],"type_original":row["type_original"],"place_text":place[:250],"own_field_roads":" | ".join(sorted(primary)),"other_text_roads":" | ".join(sorted(other)),"candidate_road":name,"review_status":status,"original_geo":row["base_geography"],"proposal":"Ingen automatisk omklassificering"})
print("OWN_FIELD_COVERAGE_QA",{"previous_reference":713,"current":len(items),"difference":len(items)-713})
assert items,"Own-field audit unexpectedly empty"
out=ROOT/"data/audit_lulea_own_place_road_qa.csv"
with out.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
print("OWN_FIELD_ROAD_QA",dict(statuses),"total",len(items))
print("TOP_OWN_FIELD_ROADS",byroad.most_common(35))
print("No published series changed")
