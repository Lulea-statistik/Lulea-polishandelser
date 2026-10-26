# Fortsatt vägrevision: Väderleden och granskningskedjan

Kontrollerat mot `docs/data/road_lengths_deso_pilot.json` (pilot 2026-10-23; OSM + SCB DeSO 2025).

## Väderleden, observationer i källfilen

| DeSO | Längd, meter |
|---|---:|
| 2580C1292 | 1 968,4 |
| 2580C1280 | 523,3 |
| 2580C1250 | 64,5 |
| **Totalt** | **2 556,2** |

Den största delsträckan utgör cirka 77,0 procent av väglängden. Vid gränsen **200 eller 500 m** finns två DeSO-delsträckor som kvalificerar; vid **1 000 m** bara en. Därför är klassificeringen tröskelkänslig. Detta räcker **inte** för att fastställa att vägen korsar stadsdelsgränser.

## Blockerande beroenden för händelsebaserad revision

Befintliga skript refererar följande filer som vid denna kontroll inte fanns under `main/data`:

- `data/audit_lulea_own_place_deso_pilot.csv`
- `data/audit_lulea_road_event_review_queue.csv`
- `data/audit_lulea_road_priority_original_evidence.csv`
- `data/gis/audit_osm_eight_roads_deso_2025.csv`

Ett framgångsrikt historiskt arbetsflöde bevisar inte att dess intermediära filer finns i dagens utcheckning. Kontrollera Actions-artifakter eller kör de befintliga skripten i korrekt beroendeordning; återställ enbart verifierade källor. **Gör inga händelsevis geografiska beslut förrän ursprunglig evidens och länken till event-ID går att återskapa.**

`python scripts/check_vaderleden_audit_dependencies.py` gör en skrivskyddad kontroll av pilotlängder, känslighet och nödvändiga indatafiler. Skriptet ändrar inte `docs/data`, `data/events.csv`, gränser eller klassificeringar. Det har ännu inte körts i CI.

Nästa GIS-steg är fortfarande jämförelse med **faktiska stadsdelsgränser**, inte ersättning med DeSO.
