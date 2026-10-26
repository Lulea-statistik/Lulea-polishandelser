#!/usr/bin/env python3
"""Reproducible read-only baseline for Lulea original and expanded area series."""
import csv
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN = "Okänt delområde"
INPUTS = {
    "ursprunglig": ROOT / "docs/data/lulea_district_monthly.csv",
    "expanderad": ROOT / "docs/data/lulea_district_expanded_monthly.csv",
}
OUT = ROOT / "data/audit_lulea_baseline_20261026.csv"
REPORT = ROOT / "docs/lulea-baslinje-20261026.md"

def measure(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert {"year", "month", "geography_group", "type_original", "event_count"} <= set(reader.fieldnames or []), path
        counts = Counter()
        rows = 0
        for record in reader:
            n = int(record["event_count"])
            assert n >= 0, record
            assert str(record["year"]).isdigit() and 1 <= int(record["month"]) <= 12, record
            counts[record["geography_group"]] += n
            rows += 1
    total = sum(counts.values())
    assert total > 0
    unknown = counts[UNKNOWN]
    assert 0 <= unknown <= total
    return {"rows": rows, "total": total, "unknown": unknown,
            "classified": total - unknown, "pct": round(100*unknown/total, 4),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    results = {name: measure(path) for name, path in INPUTS.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["serie","kalla","sha256","antal_aggregatrader","handelser","okant_delomrade","ovrigt","andel_okant_procent"])
        for name, path in INPUTS.items():
            r = results[name]
            writer.writerow([name,str(path.relative_to(ROOT)),r["sha256"],r["rows"],r["total"],r["unknown"],r["classified"],f'{r["pct"]:.4f}'])
    a,b=results["ursprunglig"],results["expanderad"]
    report = f"""# Luleå: reproducerbar baslinje för okänt delområde

Mätdefinition: summan av `event_count` i publicerade aggregerade stadsdelsserier. `Okänt delområde` jämförs med alla kategorier i respektive serie. Rapporten är **inte** en ny omklassificering och ändrar inte några geografiska beslut.

| Serie | Händelser | Okänt delområde | Andel okänt | Övriga kategorier |
|---|---:|---:|---:|---:|
| Ursprunglig | {a["total"]:,} | {a["unknown"]:,} | {a["pct"]:.2f} % | {a["classified"]:,} |
| Expanderad | {b["total"]:,} | {b["unknown"]:,} | {b["pct"]:.2f} % | {b["classified"]:,} |

Skillnad i andel okänt: {b["pct"]-a["pct"]:.2f} procentenheter (expanderad minus ursprunglig).

## Spårbarhet och reproduktion

Kör `python scripts/audit_lulea_current_baseline.py` från valfri katalog. Resultatet skrivs till `data/audit_lulea_baseline_20261026.csv`. Där registreras SHA-256 för varje indatafil, antalet aggregeringsrader och samtliga mått. Beräkningen validerar kolumner, månader och icke-negativa antal.

- Ursprunglig SHA-256: `{a["sha256"]}`.
- Expanderad SHA-256: `{b["sha256"]}`.

## Avgränsning och fortsatt platsrevision

Aggregaten mäter *publicerad klassificering*, inte kvalitetssäkrad placering av varje händelse. Ursprungs- och expanderad serie har olika populationsdefinitioner och kan inte tolkas som samma händelsemängd. Inga procenttal får användas som belägg för att geografiska gissningar förbättrar precisionen.

Nästa QA görs på händelse-ID med originalkällans platsfält, löptext och separat underhändelses plats. Dokumentera `event_id`, `parent_event_id`, före/efter-grupp, matchat uttryck, källfält, regel-id och osäkerhet. Kontrollera motsägelser, vägar genom flera områden, transporter till sjukhus och andra nämnda platser som inte är händelseplats. **Inga nya områdestilldelningar sker automatiskt.**

Datumen i filnamn är revisionsdatum; resultatet gäller de versioner av indatafilerna som identifieras av SHA-256 ovan.
"""
    REPORT.write_text(report,encoding="utf-8")
    print(report)

if __name__ == "__main__":
    main()
