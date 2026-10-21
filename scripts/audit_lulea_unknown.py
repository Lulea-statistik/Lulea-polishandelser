#!/usr/bin/env python3
"""Auditera fortfarande okända delområden utan att automatiskt ändra klassificeringen."""
import csv
import importlib.util
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("districts", ROOT/"scripts/build_lulea_districts.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
spec2=importlib.util.spec_from_file_location("places",ROOT/"scripts/audit_lulea_places.py")
places=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(places)
# Neutral platsordslista: filtrera bort ord som beskriver händelser, roller
# eller administrativa åtgärder. Detta ändrar inte stadsdel utan ger kandidater.
import re
EXCLUDE_TERMS={"olycksplatsen","brottsplatsen","polisstationen","bensinstation",
 "lansvag","riksvag","flygplatsen","fotbollsplan","trafikkontroll",
 "beordras","fordes","fors","ford","misstankt","stold","olycka","hastighetsovertradelse"}
GEOGRAPHIC_SUFFIX=re.compile(r"(?:gatan|vagen|vag|leden|bron|torget|parken|hamnen|hamn|granden|grand|stigen|kajen|plan)$")
NEUTRAL=ROOT/"data/audit_lulea_unknown_geographic_names.csv"
def neutral_name(name):
 name=name.strip()
 if any(term in name.split() for term in EXCLUDE_TERMS):return False
 if name in EXCLUDE_TERMS:return False
 if name in {"centrum","innerstaden","busstationen","busstation"}:return True
 if GEOGRAPHIC_SUFFIX.search(name):return True
 return any(name == mod.normalize(alias) for aliases in mod.ALIASES.values() for alias in aliases)
OUT=ROOT/"data/audit_lulea_unknown_candidates.csv"
SUMMARY=ROOT/"data/audit_lulea_unknown_summary.csv"
DETAIL=ROOT/"data/audit_lulea_unknown_examples.csv"
counts=defaultdict(lambda:[set(),set(),Counter(),Counter()])
summary=Counter()
examples=[]
seen=set()
with (ROOT/"data/events.csv").open(encoding="utf-8-sig",newline="") as f:
 for row in csv.DictReader(f):
  if (row.get("geography_group") or "").strip()!="Luleå kommun":continue
  eid=row.get("event_id") or ""
  if eid and eid in seen:continue
  if eid:seen.add(eid)
  summary["lulea_events"]+=1
  if mod.district(row)!=mod.UNKNOWN:continue
  summary["unknown_events"]+=1
  rawplace=" ".join(row.get(f,"") or "" for f in ("title_location","location_string"))
  rawtext=" ".join(row.get(f,"") or "" for f in ("headline","description","content"))
  p=places.mentions(rawplace)
  n=places.mentions(rawtext)
  if p:summary["unknown_with_place_candidates"]+=1
  if n:summary["unknown_with_narrative_candidates"]+=1
  if not p and not n:summary["unknown_without_candidates"]+=1
  key=eid or "row_"+str(summary["lulea_events"])
  for name in p|n:
   rec=counts[name]
   if name in p:rec[0].add(key)
   if name in n:rec[1].add(key)
   rec[2][row.get("type_original") or "Okänd"]+=1
   rec[3][row.get("year") or ""]+=1
  if len(examples)<5000:
   examples.append((key,rawplace[:220]," | ".join(sorted(p))[:250]," | ".join(sorted(n))[:250],row.get("year","")))
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f)
 w.writerow(["platsord","okanda_handelser_platsfalt","okanda_handelser_loptext","unika_okanda_handelser","vanligaste_handelsetyp","händelser_av_typen"])
 for name,rec in sorted(counts.items(),key=lambda kv:(-len(kv[1][0]|kv[1][1]),kv[0])):
  typ,k=rec[2].most_common(1)[0]
  w.writerow([name,len(rec[0]),len(rec[1]),len(rec[0]|rec[1]),typ,k])
with NEUTRAL.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["platsnamn","antal_okanda_platsfalt","antal_okanda_loptext","unika_okanda","foreslagen_stadsdel","status"])
 for name,rec in sorted(counts.items(),key=lambda kv:(-len(kv[1][0]|kv[1][1]),kv[0])):
  if not neutral_name(name):continue
  matched=[district for district,aliases in mod.ALIASES.items() if name in {mod.normalize(a) for a in aliases}]
  proposed=matched[0] if len(matched)==1 else ""
  w.writerow([name,len(rec[0]),len(rec[1]),len(rec[0]|rec[1]),proposed,"Verifiera händelseplats" if rec[0] else "Endast löptext - osäkert"])
with SUMMARY.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["matt","antal"])
 for k in ["lulea_events","unknown_events","unknown_with_place_candidates","unknown_with_narrative_candidates","unknown_without_candidates"]:
  w.writerow([k,summary[k]])
 w.writerow(["unika_platsord_i_okanda",len(counts)])
with DETAIL.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["event_id","platsfalt","kandidater_platsfalt","kandidater_loptext","ar"])
 w.writerows(examples)
print("Unknown audit:",dict(summary),"candidates:",len(counts))
