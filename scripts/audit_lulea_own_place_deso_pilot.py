#!/usr/bin/env python3
"""Join PR18 event-level road clues to pilot DeSO test, non-publishing."""
import csv,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"data/audit_lulea_own_place_road_qa.csv"
OUT=ROOT/"data/audit_lulea_own_place_deso_pilot.csv"
# Snapshot of approved audit run 39949694185, not a classification of incidents.
PILOT={
 "Hertsövägen":("egen_vaggeografi_kandidat",9,9),
 "Älvbrovägen":("egen_vaggeografi_kandidat",9,9),
 "Haparandavägen":("egen_vaggeografi_kandidat",9,9),
 "Storhedsvägen":("egen_vaggeografi_kandidat",9,9),
 "Mariebergsvägen":("egen_vaggeografi_kandidat",9,9),
 "Mjölkuddsvägen":("egen_vaggeografi_kandidat",9,9),
 "Storsandsvägen":("lokal_kandidat",9,9),
 "Väderleden":("kansligt_granskningsfall",6,9),
}
def norm(s):return str(s or "").strip().casefold()
M={norm(x):(x,*y) for x,y in PILOT.items()}
with IN.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
if not rows:raise ValueError("No candidate events in current own-place audit")
print("OWN_FIELD_DESO_INPUT_QA",{"previous_reference":713,"current":len(rows),"difference":len(rows)-713})
counts=Counter()
for row in rows:
 hit=M.get(norm(row["candidate_road"]))
 exact_one=row["review_status"]=="Entydig vägledtråd – manuell kontroll"
 if not hit:
  grade="utanför_8_vägar";road="";stable=""
 elif not exact_one:
  road,grade,yes,all_=hit
  grade="konflikt_eller_flera_vägar";stable=f"{yes}/{all_}"
 else:
  road,grade,yes,all_=hit
  stable=f"{yes}/{all_}"
 row.update({"pilot_road_name":road if hit else "","deso_test_status":grade,
             "stability_across_9":stable if hit else "",
             "decision":"Ingen publicering - kräver händelsevis kontroll av plats och väggeometri",
             "road_level_only":"Ja"})
 counts[grade]+=1
with OUT.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print("OWN_FIELD_DESO_PILOT_SUMMARY",json.dumps(dict(counts),ensure_ascii=False))
print("VADERLEDEN_REVIEW","77.0% in leading DeSO; secondary DeSO 523.3 m; classify as uncertain under 1000m sensitivity threshold")
print("NO PUBLICATION; pilot classifications are road-level hypotheses only")
