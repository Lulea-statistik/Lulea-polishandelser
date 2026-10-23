#!/usr/bin/env python3
"""Inspect C4 place strings without treating matched names as approved locations."""
import csv,re,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_hertsovagen_context_subgroups import rows
c4=[x for x in rows if x["review_subgroup"].startswith("C4")]
assert len(c4)==63,len(c4)
def group(raw):
 p=raw.casefold().strip()
 rest=re.sub(r"\bhertsövägen\b","<VÄG>",p)
 if re.fullmatch(r"<VÄG>\s*[,;/\-–]\s*[^,;/\-–]+",rest):
  return "Vägnamn plus ett efterled"
 if re.search(r"\b(?:luleå|norrbotten|hertsön)\b",rest):
  return "Har orts- eller områdesnamn"
 if re.search(r"\d",rest):
  return "Har siffra eller adressliknande tillägg"
 return "Övrig sammansatt formulering"
counts=Counter()
out=[]
for x in c4:
 g=group(x["source_place"])
 counts[g]+=1
 out.append({"event_id":x["event_id"],"source_place":x["source_place"],"context_excerpt":x["source_excerpt"],"earlier_flags":x["prior_flags"],"pattern_group":g,"decision":"Väntar på individuell källgranskning"})
assert len({x["event_id"] for x in out})==63
path=ROOT/"data/audit_lulea_hertsovagen_c4_forms.csv"
with path.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print("HERTSOVAGEN_C4_FORMS",dict(counts))
print("HERTSOVAGEN_C4_STATUS",{"pending":63,"approved":0,"published":0})
