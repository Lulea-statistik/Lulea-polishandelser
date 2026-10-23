#!/usr/bin/env python3
"""Event-level decision queue for the eight-road DeSO pilot; no publication.

Input is the audited own-place list. Road-level hypotheses never override
an explicit, conflicting or more precise event location.
"""
import csv,json,re,unicodedata
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/audit_lulea_own_place_deso_pilot.csv"
OUT=ROOT/"data/audit_lulea_road_event_review_queue.csv"
PILOT={"hertsövägen","älvbrovägen","haparandavägen","storhedsvägen","mariebergsvägen","mjölkuddsvägen","storsandsvägen","väderleden"}
def norm(x):
 x=unicodedata.normalize("NFKD",str(x or "").casefold())
 return "".join(c for c in x if not unicodedata.combining(c))
def review(row):
 place=str(row.get("place_text") or "")
 road=str(row.get("pilot_road_name") or "")
 status=row.get("deso_test_status") or ""
 if not road or norm(road) not in {norm(x) for x in PILOT}:return None
 # Text mentions of address numbers are prompts for manual evidence verification,
 # not proof of the incident's precise location.
 numbered=bool(re.search(r"\b\d{1,4}\s*[a-z]?\b",place,re.I))
 locality=bool(re.search(r"\b(?:vid|i|på|intill|nära|korsningen|rondellen|avfarten|mellan)\b",norm(place)))
 if status=="konflikt_eller_flera_vägar":
  priority,reason="P1","Flera eller motstridiga vägar; jämför originalnotis"
 elif status=="kansligt_granskningsfall":
  priority,reason="P1","Väderleden: klassificeringen beror på DeSO-tröskel"
 elif numbered or locality:
  priority,reason="P2","Möjlig mer precis platsangivelse; verifiera innan vägklass"
 else:
  priority,reason="P3","Vägledtråd utan verifierad exakt punkt"
 return {**row,"review_priority":priority,"review_reason":reason,
         "possible_specific_location":"Ja" if (numbered or locality) else "Ej identifierad",
         "evidence_rule":"Originalnotis och eget platsfält väger tyngre än generell vägklass",
         "proposed_event_geography":"Oförändrad i väntan på manuell granskning",
         "review_decision":"Ej granskad","publish":"NEJ"}
def main():
 with SOURCE.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
 if not rows:raise ValueError("Missing event-level road candidates")
 selected=[x for row in rows if (x:=review(row)) is not None]
 selected.sort(key=lambda x:(x["review_priority"],x.get("pilot_road_name",""),x.get("event_id","")))
 if not selected:raise ValueError("No pilot matches")
 if len({r["event_id"] for r in selected})!=len(selected):raise ValueError("Duplicate event IDs in pilot review")
 with OUT.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
 print("ROAD_EVENT_REVIEW_SUMMARY",json.dumps({"input":len(rows),"pilot":len(selected),"priority":dict(Counter(x["review_priority"] for x in selected)),"road":dict(Counter(x["pilot_road_name"] for x in selected)),"source_status":dict(Counter(x["deso_test_status"] for x in selected))},ensure_ascii=False))
 print("NO_PUBLICATION: Manual evidence review only")
if __name__=="__main__":main()
