#!/usr/bin/env python3
"""Generate conservative candidate review for all Lulea police publications."""
import csv
from pathlib import Path
from police_publication_dedup import candidate_pairs, REPLACED_BY

ROOT=Path(__file__).resolve().parents[1]
with (ROOT/"data/events.csv").open(encoding="utf-8-sig",newline="") as stream:
    events=[r for r in csv.DictReader(stream) if (r.get("geography_group") or "").strip()=="Luleå kommun"]
out=ROOT/"data/audit_police_publication_duplicates.csv"
candidates=list(candidate_pairs(events))
with out.open("w",encoding="utf-8",newline="") as stream:
    columns=["date","type_original","event_id_a","event_id_b","headline_similarity","a_shorter_content","review_status"]
    writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(candidates)
print("Allmän dubblettrevision, kandidater för manuell prövning:",len(candidates))
print("Bekräftade uppdateringspar:",REPLACED_BY)
for candidate in candidates[:35]:
    print("DUPLICATE_CANDIDATE",candidate["event_id_a"],candidate["event_id_b"],candidate["date"])
