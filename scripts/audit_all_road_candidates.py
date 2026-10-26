#!/usr/bin/env python3
"""Apply reusable QA flags to ALL own-place road candidates, without publication."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from road_description_review import partition_mentions

SOURCE = ROOT / "data/audit_lulea_own_place_road_qa.csv"
OUTPUT = ROOT / "data/audit_all_road_candidate_decisions.csv"

def classify(row):
    primary = [x.strip() for x in row["own_field_roads"].split("|") if x.strip()]
    candidate = primary[0] if len(primary) == 1 else ""
    if not primary:
        reason = "no_named_road_in_own_place"
    elif len(primary) > 1:
        reason = "multiple_roads_in_own_place"
    else:
        different, descriptions = partition_mentions(row["other_text_roads"], candidate)
        reason = "other_road_reference" if different else "single_own_place_road"
    return {
        "event_id": row["event_id"],
        "source": row["source"],
        "candidate_road": candidate,
        "qa_status": reason,
        "manual_review": "JA" if reason != "single_own_place_road" else "STICKPROV",
        "geography_decision": "Oförändrad",
        "publish": "NEJ",
    }

def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows, "No own-place candidate rows"
    output = [classify(row) for row in rows]
    ids = [r["event_id"] for r in output]
    assert len(ids) == len(set(ids)), "Duplicate event IDs"
    assert len(output) == len(rows)
    assert all(r["publish"] == "NEJ" for r in output)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(output[0]))
        w.writeheader()
        w.writerows(output)
    print("GENERAL_ROAD_QA", json.dumps({"total": len(output),
        "status": dict(Counter(r["qa_status"] for r in output)),
        "manual_review": dict(Counter(r["manual_review"] for r in output))}, ensure_ascii=False))
    print("NO_PUBLICATION")

if __name__ == "__main__":
    main()
