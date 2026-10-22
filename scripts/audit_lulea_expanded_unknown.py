#!/usr/bin/env python3
"""Audit unknown geography in Lulea expanded events without assigning new areas."""
import csv
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_lulea_districts import district, UNKNOWN
ROOT=Path(__file__).resolve().parents[1]
def load(path):
    with (ROOT/path).open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))
events=load("data/events.csv")
details=load("data/summary_details_dedup.csv")
lulea=lambda row:(row.get("geography_group") or "").strip()=="Luleå kommun"
rows=[]
seen=set()
for row in events:
    eid=str(row.get("event_id") or "")
    if not lulea(row) or eid in seen:continue
    seen.add(eid)
    if district(row)!=UNKNOWN:continue
    rows.append({"source":"original","event_id":eid,"parent_event_id":"","date":row.get("date",""),
      "event_type":row.get("type_original",""),"title_location":row.get("title_location",""),
      "location_string":row.get("location_string",""),"headline":row.get("headline",""),
      "place_text":"","text_excerpt":(row.get("description") or row.get("content") or "")[:280],
      "review_status":"Platsrelation ej verifierad","decision":""})
for row in details:
    if not lulea(row) or str(row.get("include_as_extra","")).lower() not in ("true","1"):continue
    specific={"title_location":row.get("place_text") or "","location_string":"",
              "headline":"","description":row.get("description") or "","content":""}
    if district(specific)!=UNKNOWN:continue
    rows.append({"source":"expanded_subevent","event_id":row.get("event_id",""),
      "parent_event_id":row.get("parent_event_id",""),"date":row.get("date",""),
      "event_type":row.get("event_type_extracted",""),"title_location":"",
      "location_string":"","headline":"","place_text":row.get("place_text",""),
      "text_excerpt":(row.get("description") or "")[:280],
      "review_status":"Underhändelsens egen plats ej verifierad","decision":""})
out=ROOT/"data/audit_lulea_expanded_unknown.csv"
out.parent.mkdir(exist_ok=True)
with out.open("w",encoding="utf-8",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]) if rows else ["source","event_id","parent_event_id","date","event_type","title_location","location_string","headline","place_text","text_excerpt","review_status","decision"])
    writer.writeheader();writer.writerows(rows)
print("Unknown candidate audit rows:",len(rows))
print("By source:",dict(Counter(r["source"] for r in rows)))
print("By event type:",Counter(r["event_type"] for r in rows).most_common(15))
print("No new geographic decisions applied.")
