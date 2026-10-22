#!/usr/bin/env python3
"""Preview exact place-reference improvements without changing publication."""
import csv,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_lulea_districts import district,UNKNOWN
root=Path(__file__).resolve().parents[1]
with (root/"data/summary_details_dedup.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
targets={"centrala luleå":"Centrum","skutvikens industriområde":"Skutviken"}
results=[]
for r in rows:
 if str(r.get("include_as_extra","")).lower() not in ("true","1") or r.get("geography_group")!="Luleå kommun":continue
 place=(r.get("place_text") or "").strip().casefold()
 if place not in targets:continue
 full={"title_location":r.get("place_text") or "","description":r.get("description") or ""}
 before=district(full)
 proposed=targets[place]
 independent=district({"title_location":r.get("place_text") or ""})
 results.append({"parent_event_id":r.get("parent_event_id",""),"place_text":place,"before":before,"proposed":proposed,"independent_classifier":independent,"safe_candidate":str(before==UNKNOWN and independent in (UNKNOWN,proposed)),"decision":"Granska manuellt"})
output=root/"data/audit_lulea_explicit_places_preview.csv"
with output.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["parent_event_id","place_text","before","proposed","independent_classifier","safe_candidate","decision"]);w.writeheader();w.writerows(results)
print("EXPLICIT_PLACE_PREVIEW",dict(Counter((r["place_text"],r["before"],r["independent_classifier"]) for r in results)))
print("Potentially improvable:",sum(x["safe_candidate"]=="True" for x in results))
print("No published geography changed.")
