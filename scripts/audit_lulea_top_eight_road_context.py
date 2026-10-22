#!/usr/bin/env python3
"""Conservative context QA for eight most frequent single-GIS-road place matches."""
import csv,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_gis_road_match_qa import rows,records,events,details,norm
TOP={"hertsövägen","älvbrovägen","haparandavägen","storhedsvägen","mariebergsvägen","mjölkuddsvägen","storsandsvägen","väderleden"}
by_id={x["event_id"]:x for x in records}
def context(event):
 key=event["event_id"]
 if event["source"]=="underhändelse":
  d=details[int(key.rsplit("#",1)[1])]
  return d.get("description") or ""
 d=events.get(key,{})
 return " ".join(d.get(k) or "" for k in ("headline","description","content"))
JUNCTION=re.compile(r"\b(?:korsning(?:en)?|korsningen mellan|trafikplats(?:en)?|avfart(?:en)?|påfart(?:en)?|rondell(?:en)?)\b",re.I)
TRAVEL=re.compile(r"\b(?:på väg till|på väg från|färdväg|fördes till|transporterades till|körde mot|i riktning mot)\b",re.I)
PLACE_RELATION=re.compile(r"\b(?:på|vid|längs|utmed|i höjd med)\b",re.I)
out=[];status=Counter();names=Counter()
for r in rows:
 road=r["gis_road_candidates"]
 if road not in TOP or not r["review_status"].startswith("En GIS-väg"):continue
 own=norm(r["place_text"]);extra=norm(context(r))
 flags=[]
 if JUNCTION.search(own):flags.append("korsning/trafikplats i platsfält")
 if TRAVEL.search(own):flags.append("färdväg i platsfält")
 if JUNCTION.search(extra):flags.append("korsning/trafikplats i text")
 if TRAVEL.search(extra):flags.append("färdväg eller transport i text")
 if not flags:flag="Inga automatiska konfliktsignaler – manuell kontroll"
 else:flag="; ".join(flags)
 status[flag]+=1;names[road]+=1
 out.append({"event_id":r["event_id"],"source":r["source"],"road_candidate":road,"original_geography":r["original_geography"],"own_place_text":r["place_text"],"text_excerpt":context(r)[:400],"review_flags":flag,"decision":"Ej verifierad; behåll nuvarande geografi"})
assert len(out)==sum(names.values())
assert len(out)==227,("Unexpected top-eight coverage",len(out))
path=ROOT/"data/audit_lulea_top_eight_road_context.csv"
with path.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print("TOP_EIGHT_ROADS",dict(names))
print("TOP_EIGHT_QA_FLAGS",dict(status))
print("PREVIEW_ONLY",{"total_events":9743,"would_move_if_all_approved":len(out),"remaining_unknown_road_if_all_approved":4279-len(out)})
