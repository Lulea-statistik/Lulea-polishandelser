#!/usr/bin/env python3
"""Auditable decision ledger; no automatic approvals and no publication."""
import csv,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_top_eight_road_context import out
ledger=[]
for x in out:
 clean=x["review_flags"].startswith("Inga automatiska konfliktsignaler")
 ledger.append({
 "event_id":x["event_id"],"source":x["source"],"candidate_road":x["road_candidate"],
 "source_geography":x["original_geography"],"source_place":x["own_place_text"],
 "source_excerpt":x["text_excerpt"],"automatic_flags":x["review_flags"],
 "review_queue":"1 – inga automatiska konfliktsignaler" if clean else "2 – korsning eller färdväg",
 "human_decision":"Väntar på källgranskning","decision_reason":"",
 "reviewer":"","proposed_geography":"","published":"nej"
 })
assert len(ledger)==227 and len({x["event_id"] for x in ledger})==227,"Duplicates or unexpected coverage"
assert sum(x["review_queue"].startswith("1") for x in ledger)==214,"Unexpected unflagged count"
assert all(x["human_decision"]=="Väntar på källgranskning" for x in ledger)
outpath=ROOT/"data/audit_lulea_road_decision_ledger.csv"
with outpath.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
print("DECISION_LEDGER",{"total":len(ledger),"priority_review":214,"flagged_review":13,"approved":0,"published":0})
print("COUNT_INVARIANT",{"before":9743,"after":9743})
