# Återskapning av befintlig väggranskning

## Varför mellanliggande filer saknas

De befintliga arbetsflödena `qa-lulea-own-place-roads.yml`, `audit-lulea-road-event-review.yml`, `audit-priority-road-original-evidence.yml` och `audit-priority-road-evidence-triage.yml` skapar granskningsfiler som **GitHub Actions-artefakter**. De behöver inte ligga i `main/data`.

Det nya arbetsflödet `rebuild-lulea-road-evidence.yml` kör samma beroendekedja i ett jobb med aktuella källfiler och arkiverar utdata tillsammans. Inga publicerade datafiler skrivs över.

## Beroendekedjan

`data/events.csv` + `data/summary_details_dedup.csv` + befintlig geografisk ordbok
→ `audit_lulea_own_place_road_qa.py`
→ `audit_lulea_own_place_deso_pilot.py`
→ `audit_lulea_road_event_review_queue.py`
→ `audit_lulea_road_priority_original_evidence.py`
→ `audit_lulea_road_priority_evidence_triage.py`.

Det geometriska revisionsunderlaget `data/gis/audit_osm_eight_roads_deso_2025.csv` ingår **inte** i denna händelsekedja, utan kan återskapas av det befintliga `audit-osm-eight-roads-deso.yml` som laddar tidigare granskade OSM-artefakter samt SCB DeSO. Det ska inte förväxlas med godkända stadsdelsgränser.

## Kontroller och återstående frågor

- Varje producerad revisionsfil måste innehålla rader och unika händelse-ID:n.
- Den slutliga triage-filen ska ha `publish = NEJ` och ingen godkänd geografisk tilldelning.
- Befintliga skript har vissa historiska fasta förväntade antal. Om antalet har ändrats efter nya polisuppdateringar ska körningen **inte** tyst godkännas; granska orsak och uppdatera därefter kontrollen med dokumenterad baslinje.
- Filen med ursprunglig polisbeskrivning är revisionsunderlag, inte publik statistik. Granska eventuella personuppgifter innan vidare distribution. Actions-artefakter i ett publikt repo ska inte behandlas som konfidentiella.
- Inga färdiga stadsdelsbeslut följer av DeSO eller vägtext ensam.

Det nya flödet har ännu inte körts och verifierats. Det kan köras via GitHub Actions efter att ändringen har införts i `main`.
