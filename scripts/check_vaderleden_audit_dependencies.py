#!/usr/bin/env python3
"""Read-only Väderleden threshold and road-audit dependency check."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "docs/data/road_lengths_deso_pilot.json"
data = json.loads(src.read_text(encoding="utf-8"))
roads = [r for r in data["rows"] if r["road"] == "Väderleden"]
assert len(roads) == 3, "Väderleden pilot has changed; review required"
total = float(roads[0]["road_total_m"])
assert all(float(r["road_total_m"]) == total for r in roads)
lengths = sorted((float(r["length_in_geography_m"]) for r in roads), reverse=True)
assert abs(sum(lengths)-total) < 1.0, "DeSO lengths do not reconcile"
print("VÄDERLEDEN", {"total_m": total, "deso_lengths_m": lengths,
                     "largest_share_pct": round(100*lengths[0]/total, 2),
                     "qualifying_at_200_m": sum(v>=200 for v in lengths),
                     "qualifying_at_500_m": sum(v>=500 for v in lengths),
                     "qualifying_at_1000_m": sum(v>=1000 for v in lengths)})
required = {
    "scripts/audit_lulea_road_event_review_queue.py": "data/audit_lulea_own_place_deso_pilot.csv",
    "scripts/audit_lulea_road_priority_original_evidence.py": "data/audit_lulea_road_event_review_queue.csv",
    "scripts/audit_lulea_road_priority_evidence_triage.py": "data/audit_lulea_road_priority_original_evidence.csv",
    "scripts/audit_road_deso_sensitivity.py": "data/gis/audit_osm_eight_roads_deso_2025.csv",
}
missing = []
for script, source in required.items():
    assert (ROOT/script).exists(), "Missing script: " + script
    if not (ROOT/source).exists():
        missing.append(source)
print("MISSING_AUDIT_INPUTS", missing)
print("STATUS: Non-publishing pilot check only; DeSO is not a district boundary.")
if missing:
    print("ACTION: Recreate audit inputs from existing upstream scripts or restore verified audit artifacts before event-level review.")
