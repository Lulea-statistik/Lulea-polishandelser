# Baslinje: okänt delområde (26 oktober 2026)

Kontroll av de två publicerade aggregerade filerna på main vid revisionstillfället:

| Serie | Händelser | Okänt delområde | Andel okänt |
|---|---:|---:|---:|
| Ursprunglig | 6 224 | 2 469 | 39,67 % |
| Expanderad | 9 750 | 5 309 | 54,45 % |

Skillnad: 14,78 procentenheter. Uppgifterna bygger på `docs/data/lulea_district_monthly.csv` respektive `docs/data/lulea_district_expanded_monthly.csv`. Mätningen gäller publicerade aggregat, inte nya geografiska beslut.

Reproducera med `python scripts/audit_lulea_current_baseline.py`. Skriptet validerar kolumner, månadsformat, icke-negativa antal och skriver både CSV med SHA-256 för indata samt metodrapport. **Skriptet är ännu inte exekverat av denna PR**, så de genererade filerna är inte committade.

Platsrevision: ingen händelse flyttas från okänt utan explicit belägg för faktisk händelseplats. Jämför event-id, originaltext, underhändelser och negativa kontroller innan någon ändring av klassificeringsregler görs.