#!/usr/bin/env python3
"""Non-publishing sensitivity test of DeSO road classification thresholds.

Uses historical, successful road-geometry audit. No event assignment is changed.
"""
import csv
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/gis/audit_osm_eight_roads_deso_2025.csv"
OUT=ROOT/"data/gis"
SECONDARY_THRESHOLDS=(200,500,1000)
DOMINANCE_THRESHOLDS=(0.80,0.90,0.95)
MIN_ROAD_M=2000
def classify(total,parts,dominance,secondary):
 if not parts or total<=0:return "osaker"
 ordered=sorted(parts.values(),reverse=True)
 primary=ordered[0]
 runner=ordered[1] if len(ordered)>1 else 0
 share=primary/total
 # Conservative separation: no zone between certainty bands is silently reclassified.
 if share>=dominance and runner<=secondary:return "lokal_kandidat"
 if total>=MIN_ROAD_M and share<=0.80 and runner>=secondary:return "egen_vaggeografi_kandidat"
 return "osaker"
def main():
 if not SRC.exists():raise SystemExit("Missing audited DeSO CSV; run archive audit first")
 with SRC.open(encoding="utf-8",newline="") as f:records=list(csv.DictReader(f))
 if len(records)!=8:raise ValueError("Expected eight road audits")
 results=[]
 for row in records:
  name=row["road_name"]
  lengths=json.loads(row["deso_lengths_m"])
  total=float(row["inside_lulea_m"])
  if total<=0 or not lengths:raise ValueError("Missing geometry for "+name)
  if abs(sum(lengths.values())-total)>max(10,total*.02):raise ValueError("DeSO overlay coverage mismatch for "+name)
  ordered=sorted(lengths.items(),key=lambda kv:-kv[1])
  for dominance in DOMINANCE_THRESHOLDS:
   for secondary in SECONDARY_THRESHOLDS:
    results.append({"road_name":name,"total_m":round(total,1),"main_deso":ordered[0][0],
     "main_share_pct":round(100*ordered[0][1]/total,1),
     "second_deso":ordered[1][0] if len(ordered)>1 else "",
     "second_length_m":round(ordered[1][1],1) if len(ordered)>1 else 0,
     "local_dominance_pct":int(dominance*100),"secondary_threshold_m":secondary,
     "classification":classify(total,lengths,dominance,secondary),
     "publish":"NEJ"})
 if len(results)!=72:raise AssertionError(len(results))
 with (OUT/"audit_road_deso_sensitivity.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=results[0]);w.writeheader();w.writerows(results)
 summary=[]
 for dominance in DOMINANCE_THRESHOLDS:
  for secondary in SECONDARY_THRESHOLDS:
   selected=[r for r in results if r["local_dominance_pct"]==int(dominance*100) and r["secondary_threshold_m"]==secondary]
   count=Counter(r["classification"] for r in selected)
   summary.append({"dominance_pct":int(dominance*100),"secondary_m":secondary,**count})
 with (OUT/"audit_road_deso_sensitivity_summary.csv").open("w",newline="",encoding="utf-8") as f:
  cols=["dominance_pct","secondary_m","lokal_kandidat","egen_vaggeografi_kandidat","osaker"]
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for v in summary:w.writerow({k:v.get(k,0) for k in cols})
 print("DESO_SENSITIVITY_SUMMARY",json.dumps(summary,ensure_ascii=False))
 for name in sorted({r["road_name"] for r in results}):
  selected=[x for x in results if x["road_name"]==name]
  print("DESO_SENSITIVITY_ROAD",json.dumps({"road":name,"main_share_pct":selected[0]["main_share_pct"],
   "second_length_m":selected[0]["second_length_m"],
   "outcomes":dict(Counter(x["classification"] for x in selected))},ensure_ascii=False))
 print("NO_PUBLICATION: classification candidates only, require geometry & event review")
if __name__=="__main__":main()
