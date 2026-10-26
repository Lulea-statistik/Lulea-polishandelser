#!/usr/bin/env python3
"""Read-only smoke test for the standalone Lulea transport page and published CSV."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "docs/transport.html").read_text(encoding="utf-8")
data = ROOT / "docs/data/lulea_transport_monthly.csv"
expected = {"year", "geography_group", "location_precision", "road_reference",
            "junction_reference", "transport_mode", "event_kind", "review_status", "event_count"}
with data.open(encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    cols = set(reader.fieldnames or [])
    assert expected <= cols, f"Missing fields: {expected - cols}"
    total = 0
    for row in reader:
        n = int(row["event_count"])
        assert n >= 0
        total += n
assert total > 0, "No transport data"
for f in expected:
    assert ("r." + f) in page or ("'" + f + "'") in page or ('"' + f + '"') in page, f"Page missing field reference: {f}"
assert "data/lulea_transport_monthly.csv" in page
for name in ("docs/index.html", "docs/lulea.html"):
    text = (ROOT / name).read_text(encoding="utf-8")
    assert 'href="transport.html"' in text, name
print(f"PASS: standalone transport page, navigation and dataset fields; {total} category matches")
