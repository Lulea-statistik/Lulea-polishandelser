#!/usr/bin/env python3
"""Hertsoevagen source-oriented review queue: candidate evidence, not automatic approval."""
import csv,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_road_decision_ledger import ledger
target=[dict(x) for x in ledger if x["candidate_road"]=="hertsövägen"]
assert len(target)==73,len(target)
assert len({x["event_id"] for x in target})==73
# Only exact isolated place text can be identified as a simple road label.
# Even this does not prove the road is an event location, so retain pending decision.
SIMPLE=re.compile(r"^\s*hertsövägen\s*[\.,;:]?\s*$",re.I)
PREP=re.compile(r"^\s*(?:på|vid|längs|utmed)\s+hertsövägen\s*[\.,;:]?\s*$",re.I)
counts=Counter()
for x in target:
 place=x["source_place"].strip()
 if SIMPLE.fullmatch(place):level="A – endast vägnamn i platsfält"
 elif PREP.fullmatch(place):level="B – tydlig vägpreposition i platsfält"
 else:level="C – övrig eller sammansatt platsuppgift"
 if x["automatic_flags"].startswith("Inga automatiska"):context="Ingen tidigare konfliktflagga"
 else:context="Tidigare konfliktflagga – särskild granskning"
 x["source_form"]=level;x["context_screen"]=context
 x["human_decision"]="Väntar på individuell källgranskning"
 x["decision_reason"]=""
 x["published"]="nej"
 counts[(level,context)]+=1
path=ROOT/"data/audit_lulea_hertsovagen_case_review.csv"
with path.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(target[0]));w.writeheader();w.writerows(target)
print("HERTSOVAGEN_CASES",len(target))
print("HERTSOVAGEN_SOURCE_FORMS",dict(counts))
print("HERTSOVAGEN_DECISIONS",{"review_pending":73,"approved":0,"published":0})
assert all(x["human_decision"].startswith("Väntar") for x in target)
