# Verifierad aggregatkontroll – 2026-10-26

Kontrollen har utförts mot aktuell `main` via GitHub-anslutningen, med separat CSV-parsning och verifiering av aggregeringsnycklarna `year,month,geography_group,type_original`. Detta är en oberoende kontroll av publicerade aggregat, **inte** en lokal körning av Python-skriptet och inte en händelse-ID-revision.

| Serie | Rader | Händelser | Okänt | Andel okänt |
|---|---:|---:|---:|---:|
| Ursprunglig | 4 440 | 6 224 | 2 469 | 39,6690 % |
| Expanderad | 5 579 | 9 750 | 5 309 | 54,4513 % |

Skillnaden är **14,7823 procentenheter**. Felaktiga CSV-rader: 0; dubbla aggregeringsnycklar: 0; negativa händelseantal: 0, i båda filerna.

Indata identifieras med Git blob SHA i `data/audit_lulea_baseline_verified_20261026.csv`. Skriptet `scripts/audit_lulea_current_baseline.py` genererar dessutom SHA-256 när det körs lokalt eller i CI, men den körningen är ännu inte utförd.

## Observerade kategorier
- Ursprunglig: Centrum 877, Storheden 447, Hertsön 246, Flera stadsdelar i Luleå 205.
- Expanderad: Centrum 1 171, Storheden 465, Hertsön 292, Flera stadsdelar i Luleå 206.

`Flera stadsdelar i Luleå` ingår i övriga kategorier, men representerar inte en enda säker stadsdel. Måttet `handelser - okant` är därför **inte** liktydigt med antal händelser säkert knutna till en viss stadsdel.

## Nästa granskning

1. Läs råa `data/events.csv` och `data/summary_details_dedup.csv` i reproducerbar körmiljö, verifiera originalseriens event-ID-deduplicering och expansionsregler.
2. Ta fram händelse-ID-granskningskö med platsfält, beskrivning och explicit källa, men undvik publicering av onödiga personuppgifter.
3. Granska exempel på Innerstaden/Centrum, Sunderbyn/sjukhus och vägpassager som **negativa kontroller**.
4. Ändra endast klassificeringsregler efter dokumenterad manuell evidens, och kör då regressionstest på alla år.

Ingen automatisk geografisk omklassificering har genomförts.
