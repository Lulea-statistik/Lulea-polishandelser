# Revisionsnotering – upprepade vägnamn, 2026-10-26

Granskad GitHub Actions-artefakt: körning 40308479823, artefakt 12642324553. Artefakten innehöll 714 egna platsfält med vägkandidater, 231 poster i åttavägspiloten och 20 prioriterade P1/P2-poster. För dessa 20 var automatikens klasser 10 `flera_vaguppgifter` och 10 `enbart_väg_ledtråd`.

**Identifierad risk:** I ett antal granskade poster upprepar `other_road_mentions` samma väg som `pilot_road`. Det ska inte ensamt ge status som motsägelse eller flera *olika* vägar. Den ursprungliga texten och alla originalfält ska ändå bevaras. Ett andra distinkt vägnamn eller en annan geografisk relation kräver fortsatt manuell granskning.

Exempel på händelse-ID för ny kontroll:

| Event-ID | Kandidatväg | Förekomst | Revisionsåtgärd |
|---|---|---|---|
| 117380 | Väderleden | Pilotvägen upprepas i kompletterande vägfält | Jämför normaliserade vägnamn, inte bara om fältet är ifyllt |
| 18937 | Väderleden | Pilotvägen upprepas | Samma kontroll |
| 55290 | Mjölkuddsvägen | Även väg 97 förekommer | Behåll som faktisk andra vägledtråd, kontrollera korsningsrelation |
| 110870 | Storsandsvägen | Även Karlviksvägen förekommer | Behåll som separat vägledtråd |

Detta är **triage av redan extraherade källfält**, inte beslut om händelseplats.

Förslag till regressionskrav: normalisera Unicode, accenttecken och versaler i vägnamn; dela övriga vägomnämnanden vid pipe-tecken; filtrera endast bort exakt identiska upprepningar av pilotvägens namn; behåll alla andra omnämnanden i manuell kö. Inga geografiska tilldelningar sker automatiskt.

Kör den samlade granskningskedjan igen efter kodändringen och jämför P1/P2-fördelning händelsevis innan publicering.
