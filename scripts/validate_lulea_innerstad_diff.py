#!/usr/bin/env python3
"""Compare district classifications on current branch with main, event by event."""
import csv
import importlib.util
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_lulea_districts import district as updated, UNKNOWN

baseline_source = subprocess.check_output(
    ["git", "show", "origin/main:scripts/build_lulea_districts.py"], text=True
)
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "district_baseline.py"
    p.write_text(baseline_source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("district_baseline", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before = module.district

    changes = []
    totals = Counter()
    old_unknown = new_unknown = 0
    seen = set()
    with (ROOT / "data/events.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("geography_group") or "").strip() != "Luleå kommun":
                continue
            eid = str(row.get("event_id") or "").strip()
            if eid and eid in seen:
                continue
            if eid:
                seen.add(eid)
            old, new = before(row), updated(row)
            totals["events"] += 1
            old_unknown += old == UNKNOWN
            new_unknown += new == UNKNOWN
            if old != new:
                changes.append((eid, old, new, row.get("headline", "")[:100]))
                totals[(old, new)] += 1

    print("Lulea events:", totals["events"])
    print("Unknown before:", old_unknown, "after:", new_unknown)
    print("Changed events:", len(changes))
    for (a, b), n in sorted(((k, v) for k, v in totals.items() if isinstance(k, tuple)), key=lambda x: -x[1]):
        print("Transition:", a, "->", b, n)
    for r in changes[:30]:
        print("Example:", repr(r))
    assert totals["events"] > 0, "Missing Lulea events"
    assert all(old == UNKNOWN and new == "Centrum" for _, old, new, _ in changes), "Unexpected changes in other districts"
    assert old_unknown - new_unknown == len(changes), "Count mismatch"
    print("PASS: all transitions are Unknown -> Centrum, same number of input events.")
