#!/usr/bin/env python3
"""Reconcile the existing eight-road DeSO pilot; NEVER approve district geography."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/data/road_lengths_deso_pilot.json"
OUTPUT = ROOT / "data/audit_eight_road_pilot_coverage.csv"
EXPECTED = {"Hertsövägen", "Älvbrovägen", "Haparandavägen", "Storhedsvägen",
            "Mariebergsvägen", "Mjölkuddsvägen", "Storsandsvägen", "Väderleden"}

def calculate():
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert payload["metadata"]["as_of"] == "2026-10-23"
    buckets = defaultdict(list)
    for row in payload["rows"]:
        buckets[row["road"]].append(row)
    assert set(buckets) == EXPECTED, "Pilot road set changed: review inputs"
    result = []
    for name in sorted(buckets):
        rows = buckets[name]
        codes = [x["geography_code"] for x in rows]
        assert len(codes) == len(set(codes)), "Duplicate road/DeSO: " + name
        totals = {float(x["road_total_m"]) for x in rows}
        assert len(totals) == 1, "Inconsistent total: " + name
        total = totals.pop()
        covered = sum(float(x["length_in_geography_m"]) for x in rows)
        delta = round(covered - total, 2)
        assert total > 0 and all(float(x["length_in_geography_m"]) >= 0 for x in rows)
        assert abs(delta) <= max(2.0, total * .001), "Length reconciliation failed: " + name
        result.append({
            "road": name,
            "deso_count_in_snapshot": len(codes),
            "road_total_m": round(total, 1),
            "sum_deso_lengths_m": round(covered, 1),
            "difference_m": delta,
            "deso_observation": "Flera DeSO i pilotunderlag" if len(codes) > 1 else "Ett DeSO i pilotunderlag",
            "district_status": "Ej verifierad - stadsdelsgränser saknas",
            "special_review": "Känsligt tröskelfall" if name == "Väderleden" else "Inga automatiska stadsdelsbeslut",
            "publish": "NEJ",
        })
    return result

def main():
    result = calculate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=result[0])
        writer.writeheader()
        writer.writerows(result)
    print(json.dumps({"pilot_roads": len(result),
                      "multiple_deso": sum(x["deso_count_in_snapshot"] > 1 for x in result),
                      "single_deso": sum(x["deso_count_in_snapshot"] == 1 for x in result),
                      "max_absolute_reconciliation_m": max(abs(x["difference_m"]) for x in result),
                      "published_changes": 0}, ensure_ascii=False))
    print("NO PUBLICATION: no event geography or district classification modified")

if __name__ == "__main__":
    main()
