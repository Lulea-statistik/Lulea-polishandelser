#!/usr/bin/env python3
"""Inventory possible named roads within still-unknown road geography; no publication."""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_lulea_unified_geography_preview import records, ROAD_REFERENCES
ROOT=Path(__file__).resolve().parents[1]
events={}
with (ROOT/"data/events.csv").open(encoding="utf-8-sig",newline="") as f:
 for r in csv.DictReader(f):events[str(r.get("event_id") or "").strip()]=r
details=[]
with (ROOT/"data/summary_details_dedup.csv").open(encoding="utf-8-sig",newline="") as f:details=list(csv.DictReader(f))
# Capture complete place names, not generic 'väg' and not arbitrary narrative.
ROAD_WORD=re.compile(r"(?<!\w)([A-Za-zÅÄÖåäö][A-Za-zÅÄÖåäö\-]{2,}(?:vägen|väg|leden|led|gatan|gata|gränd|granden|bron|banken))\b",re.I)
ROAD_NO=re.compile(r"\b(?:(?:riks|läns)?väg(?:en)?\s*(?:nr\.?\s*)?|rv\s*)(\d{2,4})\b",re.I)
ALIASES={"svartöleden":"Svartövägen / Svartöleden"}
results=Counter(); examples=defaultdict(list); hits=Counter()
for row in records:
 if row["classification"]!="väg-okänd":continue
 eid=row["event_id"]
 if row["source"]=="underhändelse":
  try:d=details[int(eid.rsplit("#",1)[1])]
  except (ValueError,IndexError):continue
  primary=d.get("place_text") or ""
  extra=d.get("description") or ""
 else:
  d=events.get(eid,{})
  primary=" ".join(d.get(k) or "" for k in ("title_location","location_string"))
  extra=" ".join(d.get(k) or "" for k in ("headline","description"))
 found_primary={ALIASES.get(x.casefold(),x.casefold()) for x in ROAD_WORD.findall(primary) if x.casefold() not in ("riksväg","länsväg","landsväg")}
 found_primary.update("Väg "+x for x in ROAD_NO.findall(primary))
 found_extra={ALIASES.get(x.casefold(),x.casefold()) for x in ROAD_WORD.findall(extra) if x.casefold() not in ("riksväg","länsväg","landsväg")}
 found_extra.update("Väg "+x for x in ROAD_NO.findall(extra))
 for name in found_primary:
  results[(name,"Eget platsfält")]+=1
  if len(examples[(name,"Eget platsfält")])<5:examples[(name,"Eget platsfält")].append(eid)
 for name in found_extra-found_primary:
  results[(name,"Bara övrig text - måste verifieras")]+=1
  if len(examples[(name,"Bara övrig text - måste verifieras")])<5:examples[(name,"Bara övrig text - måste verifieras")].append(eid)
 if found_primary:hits["eget platsfält"]+=1
 elif found_extra:hits["bara text"]+=1
 else:hits["utan namngiven vägledtråd"]+=1
out=ROOT/"data/audit_lulea_unknown_road_names.csv"
with out.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["road_candidate","evidence_location","event_count","example_event_ids","decision"])
 for (name,kind),n in sorted(results.items(),key=lambda x:(-x[1],x[0][0])):
  w.writerow([name,kind,n," | ".join(examples[(name,kind)]),"Ej geografiskt verifierad"])
print("UNKNOWN_ROAD_DISCOVERY",dict(hits))
print("Top candidates",[(k,v) for k,v in results.most_common(35)])
for n in (596,599,607,970,616,583,584,582,573,960,563,577,576,575,580,581,600,383,687,601,692,691,768,356,780,695):
 print("NUMBERED_ROAD",n,"own_field",results.get(("Väg "+str(n),"Eget platsfält"),0),"other_text",results.get(("Väg "+str(n),"Bara övrig text - måste verifieras"),0))
assert not any(name.casefold() in ("riksväg","länsväg") for name,_ in results),"Generic road type falsely detected as named road"
print("Saved",out)
