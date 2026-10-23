#!/usr/bin/env python3
"""Analyze actual place-text suffixes for 63 Hertsovagen C4 cases; no decision."""
import csv,re,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_hertsovagen_context_subgroups import rows
c4=[x for x in rows if x["review_subgroup"].startswith("C4")]
assert len(c4)==63
def classify(place):
 s=re.sub(r"\s+"," ",place.casefold().strip().strip(" ,.;"))
 # Police location strings often prefix street names with the municipality.
 s=re.sub(r"^luleå\s+(?=hertsövägen\b)","",s)
 if re.fullmatch(r"hertsövägen\s*,\s*luleå\s*,\s*norrbottens län",s):
  return "Väg + kommun + län (standardformat)"
 if re.fullmatch(r"hertsövägen\s*,\s*luleå",s):
  return "Väg + kommun"
 if re.fullmatch(r"hertsövägen\s*,\s*hertsön(?:\s*,\s*luleå)?",s):
  return "Väg + stadsdel"
 if re.fullmatch(r"hertsövägen\s*,\s*[^,]+\s*,\s*luleå\s*,\s*norrbottens län",s):
  return "Väg + namngiven plats/verksamhet + kommun + län"
 if re.search(r"\b(?:korsning|rondell|trafikplats|mot|från|till|mellan|via)\b",s):
  return "Färdväg eller trafikkoppling"
 return "Övrigt – kontrollera platsfält"

counts=Counter(); examples=defaultdict(list);out=[]
for x in c4:
 group=classify(x["source_place"]);counts[group]+=1
 if len(examples[group])<5:examples[group].append(x["source_place"])
 out.append({"event_id":x["event_id"],"source_place":x["source_place"],"pattern_group":group,"context_excerpt":x["source_excerpt"],"previous_flags":x["prior_flags"],"decision":"Ej beslutad"})
assert len({x["event_id"] for x in out})==63
path=ROOT/"data/audit_lulea_hertsovagen_c4_exact_patterns.csv"
with path.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print("HERTSOVAGEN_C4_EXACT_PATTERNS",dict(counts))
for group,samples in sorted(examples.items()):print("HERTSOVAGEN_C4_EXAMPLES",group,repr(samples))
assert sum(counts.values())==63
print("C4_DECISIONS",{"pending":63,"approved":0,"published":0})
