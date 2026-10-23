#!/usr/bin/env python3
"""Non-publishing original-evidence review of priority P1/P2 police road events."""
import csv,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def read(path):
 with (ROOT/path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
queue=read("data/audit_lulea_road_event_review_queue.csv")
events={str(x.get("event_id","")).strip():x for x in read("data/events.csv")}
details=read("data/summary_details_dedup.csv")
rows=[]
for q in queue:
 if q["review_priority"] not in ("P1","P2"):continue
 eid=q["event_id"]
 if q["source"]=="underhändelse":
  try:
   detail=details[int(eid.rsplit("#",1)[1])]
   assert str(detail.get("parent_event_id","")).strip()==eid.rsplit("#",1)[0]
  except (IndexError,ValueError,AssertionError):
   raise ValueError("Cannot safely resolve subevent ID "+eid)
  original=events.get(eid.rsplit("#",1)[0],{})
  narrative=detail.get("description","")
  source_location=detail.get("place_text","")
 else:
  original=events.get(eid)
  if original is None:raise ValueError("Unresolved original event "+eid)
  narrative=" ".join(str(original.get(k) or "") for k in ("headline","description","content"))
  source_location=" | ".join(str(original.get(k) or "") for k in ("title_location","location_string"))
 # Read-only document evidence, not evidence of precise spatial point.
 rows.append({"event_id":eid,"priority":q["review_priority"],"pilot_road":q["pilot_road_name"],
  "source":q["source"],"original_place_field":source_location,
  "audit_place_field":q["place_text"],"original_narrative":narrative,
  "other_road_mentions":q.get("other_text_roads",""),"original_geo":q.get("original_geo",""),
  "review_reason":q["review_reason"],"evidence_status":"Ursprungstext hämtad - ej manuellt beslutad",
  "recommended_action":"Verifiera den faktiska platsangivelsen; geometri ensam räcker inte",
  "proposed_geography":"Oförändrad","publish":"NEJ"})
rows.sort(key=lambda x:(x["priority"],x["pilot_road"],x["event_id"]))
assert len(rows)==len({x["event_id"] for x in rows}),"Duplicate priority event IDs"
with (ROOT/"data/audit_lulea_road_priority_original_evidence.csv").open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print("ROAD_PRIORITY_ORIGINAL_EVIDENCE",json.dumps({"total":len(rows),"priorities":dict(Counter(x["priority"] for x in rows)),"roads":dict(Counter(x["pilot_road"] for x in rows))},ensure_ascii=False))
print("NO PUBLICATION: audit and original text only")
