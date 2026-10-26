# Fortsättning: åtta vägars DeSO-pilot – 2026-10-26

Den befintliga filen `docs/data/road_lengths_deso_pilot.json` har granskats utan att samla in nya vägdata. Källfilen anger 2026-10-23, OSM + SCB DeSO 2025, GitHub Actions-körning 39943357987.

## Kontrollresultat

- Åtta unika pilotvägar och 33 unika väg–DeSO-kombinationer.
- Sju vägar har längdbidrag i flera DeSO i pilotunderlaget; Storsandsvägen har ett.
- Summa delsträckslängder avviker högst 0,2 meter från vägarnas redovisade totallängd (avrundning).
- Väderleden är redan markerad som känsligt gränsfall i den befintliga känslighetsanalysen.
- **Ingen väg är härmed verifierad som områdesöverskridande mellan stadsdelar.** DeSO och stadsdel är olika områdesindelningar.

## Reproduktion

Kör `python scripts/audit_eight_road_pilot_coverage.py` för att skapa `data/audit_eight_road_pilot_coverage.csv` från den befintliga JSON-filen. Kontrollskriptet testar åtta förväntade vägnamn, unik väg/DeSO-kombination, konsistenta totallängder samt fullständighet inom avrundningstolerans.

`data/audit_eight_road_pilot_coverage_verified.csv` innehåller en oberoende genomräkning av JSON-underlaget. Den är inte utdata från en verifierad Python-körning.

## Fortsatt arbete – knyt an till befintlig granskning

1. Utgå från `scripts/audit_lulea_road_event_review_queue.py` och `scripts/audit_lulea_road_priority_original_evidence.py`; behåll deras händelse-ID och ursprungliga platsuppgift som spårbar grund.
2. Verifiera verkliga stadsdelsgränser/av kommun godkänd områdesindelning mot geometrin för de redan granskade pilotvägarna. **DeSO-överlapp räcker inte** för att besluta väggeografi.
3. Granska först konfliktfall och Väderleden. Dokumentera vägsträcka, stadsdelsgränser, underlag, event-ID, beslut och skäl.
4. E4, väg 94, väg 97 är prioriterade geografier enligt beslutad metod; de ingår **inte automatiskt** i den åttavägspilot som detta dokument avser.
5. Efter manuellt styrkt beslut: regressionstesta hela ursprungs- och expanderad serie. Ändra inte publicerade geografier utifrån denna pilotrapport.

Publiceringsbeslut: **NEJ**. Denna fortsättning gäller QA av äldre underlag, inte nya geokodningar.
