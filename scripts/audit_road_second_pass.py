#!/usr/bin/env python3
"""Second-pass road review queue and deterministic quality sample; never publishes."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"data/audit_lulea_own_place_road_qa.csv"
QUEUE=ROOT/"data/audit_road_exceptions_second_pass.csv"
SAMPLE=ROOT/"data/audit_road_normal_sample.csv"
SAMPLE_SIZE=30

def split_names(text):
    return [part.strip() for part in (text or "").split("|") if part.strip()]

def triage(row):
    own=split_names(row.get("own_field_roads"))
    other=split_names(row.get("other_text_roads"))
    if len(own)>1:
        reason="multiple_roads_in_place"
    elif len(own)==1:
        from road_description_review import partition_mentions
        different,_=partition_mentions(row.get("other_text_roads"),own[0])
        reason="other_road_in_description" if different else "normal"
    else:
        reason="missing_own_road"
    place=(row.get("place_text") or "").casefold()
    junction=any(term in place for term in ("korsning","rondell","trafikplats","avfart","påfart","mellan "))
    subtype=("possible_junction" if junction else "other_road_relation_unclear") if reason in ("multiple_roads_in_place","other_road_in_description") else "sample"
    return {"event_id":row["event_id"],"source":row["source"],"candidate_road":row.get("candidate_road",""),
            "qa_status":reason,"review_subtype":subtype,
            "review_decision":"Ej beslutad","geography_decision":"Oförändrad","publish":"NEJ"}

def main():
    from sys import path
    path.insert(0,str(ROOT/"scripts"))
    with INPUT.open(encoding="utf-8-sig",newline="") as f:
        source=list(csv.DictReader(f))
    assert source
    all_rows=[triage(row) for row in source]
    assert len({r["event_id"] for r in all_rows})==len(all_rows)
    exceptions=[r for r in all_rows if r["qa_status"]!="normal"]
    normal=[r for r in all_rows if r["qa_status"]=="normal"]
    normal.sort(key=lambda r:(hashlib.sha256(("lulea-road-qa-v1:"+r["event_id"]).encode()).hexdigest(),r["event_id"]))
    chosen=normal[:min(SAMPLE_SIZE,len(normal))]
    assert len(exceptions)+len(normal)==len(source)
    assert all(r["publish"]=="NEJ" and r["geography_decision"]=="Oförändrad" for r in all_rows)
    for path,rows in ((QUEUE,exceptions),(SAMPLE,chosen)):
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(all_rows[0]))
            writer.writeheader();writer.writerows(rows)
    print("ROAD_SECOND_PASS",json.dumps({"input":len(source),"exceptions":len(exceptions),"normal":len(normal),
        "exception_subtypes":dict(Counter(x["review_subtype"] for x in exceptions)),
        "sample":len(chosen),"publish":0},ensure_ascii=False))

if __name__=="__main__": main()
