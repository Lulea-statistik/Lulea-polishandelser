#!/usr/bin/env python3
"""Split 73 Hertsovagen candidate locations into reviewable phrase forms, no publication."""
import csv,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_hertsovagen_case_review import target
def classify(place):
 p=str(place).casefold().strip()
 if re.fullmatch(r"hertsövägen\s*[\.,;:]?",p):return "A – exakt vägnamn"
 if re.search(r"\b(?:korsning|korsningen|rondell|trafikplats|avfart|påfart)\b",p):return "C1 – korsning eller trafikplats i platsfält"
 if re.search(r"\b(?:mot|från|till|mellan|via|riktning)\b",p):return "C2 – möjlig färdväg eller flera platser"
 if re.search(r"\b(?:på|vid|längs|utmed|i höjd med)\s+hertsövägen\b",p):return "C3 – väg med platsrelation och tillägg"
 return "C4 – annan sammansatt platsuppgift"
rows=[];totals=Counter()
for x in target:
 label=classify(x["source_place"])
 totals[label]+=1
 rows.append({"event_id":x["event_id"],"road":"Hertsövägen","source_place":x["source_place"],"source_excerpt":x["source_excerpt"],"prior_flags":x["automatic_flags"],"review_subgroup":label,"manual_decision":"Väntar på källgranskning","reason":""})
assert len(rows)==73 and len({x["event_id"] for x in rows})==73
assert sum(totals.values())==73
path=ROOT/"data/audit_lulea_hertsovagen_context_subgroups.csv"
with path.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print("HERTSOVAGEN_SUBGROUPS",dict(totals))
print("HERTSOVAGEN_REVIEW_STATUS",{"pending":73,"approved":0,"published":0})
