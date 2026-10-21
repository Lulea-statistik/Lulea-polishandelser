#!/usr/bin/env python3
"""Spårbar platsledtrådsrevision för okända Luleåhändelser.

Inspirerad av Statistik-utstationerings separata granskningskandidater:
inga externa geokodare, inget övertagande av koordinater och ingen
automatisk omklassning. Här sparas endast uttryck och källfält.
"""
import csv,re,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_lulea_districts import district,UNKNOWN,normalize
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/audit_lulea_unknown_context_candidates.csv"
SUMMARY=ROOT/"data/audit_lulea_unknown_context_summary.csv"
NAMES={
"ort_eller_by":r"\\b(?:rutvik|person|bensbyn|bjorsbyn|sinksundet|lulsundet|kallax|alvik|antnas|ersnas|mattsund|ale|avan|balinge|jamt[oö]n|vit[aå]|niemisel|str[oö]msund|pr[aä]stholm|sundom|smedsbyn|brandon|orarna|sunderbyn|b[oö]rjelslandet)\\b",
"byggnad_eller_verksamhet":r"\\b(?:systembolaget|coop arena|coop forum|ica maxi|willys|postnord|ssab|teknikens hus|kulturens hus|stadshuset|musikomat|shell|circle k|okq8|sunderby sjukhus)\\b",
"evenemang":r"\\b(?:lulea live|splash lulea|under solen|rix fm festival|musikfestivalen i lulea|musikens makt|luleakalaset|hamnfestivalen)\\b",
"platsbeskrivning":r"\\b(?:korsningen|rondellen|trafikplats|parkeringen|parkeringshuset|busshallplats|stationen|vid skolan|idrottsplatsen|fotbollsplan|badplats|hamnen|bron)\\b",
"adressfragment":r"\\b[a-z]{3,35}(?:gatan|vagen|grand|stigen|leden)\\s+[0-9]{1,4}[a-z]?\\b",
}
# Expressions normalized with NFKD by normalize(), so only ASCII.
NAMES={k:re.compile(v.replace('\\\\','\\')) for k,v in NAMES.items()}
counts=Counter(); examples=[]
with (ROOT/"data/events.csv").open(encoding="utf-8-sig",newline="") as f:
 seen=set()
 for row in csv.DictReader(f):
  if row.get("geography_group")!="Luleå kommun" or district(row)!=UNKNOWN:continue
  eid=row.get("event_id","")
  if eid in seen and eid:continue
  if eid:seen.add(eid)
  for field in ("title_location","location_string","headline","description","content"):
   raw=row.get(field) or ""
   for typ,pat in NAMES.items():
    for m in pat.finditer(normalize(raw)):
     name=m.group(0)
     counts[(typ,name,field)]+=1
     if len(examples)<15000:examples.append([eid,row.get("year",""),field,typ,name,raw[:220]])
with OUT.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["event_id","year","source_field","clue_type","matched_text","source_excerpt"]);w.writerows(examples)
with SUMMARY.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["clue_type","matched_text","source_field","occurrences","recommendation"])
 for (typ,name,field),count in counts.most_common():
  w.writerow([typ,name,field,count,"Granska platsrelation och extern adresskalla; ej automatiskt klassificerad"])
print("Geographic context evidence rows:",len(examples),"summary groups:",len(counts))
