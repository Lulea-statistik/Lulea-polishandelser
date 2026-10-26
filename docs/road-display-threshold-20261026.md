# Visning av väggeografi

Beslutad visningsgräns: 10 registrerade kategoriträffar under samtliga år.

- Namngivna vägar med minst 10 träffar redovisas separat i geografimenyn.
- Namngivna vägar med 1–9 träffar redovisas som Övrig väg, känd väg.
- Saknat identifierbart vägnamn redovisas som Övrig väg, okänd väg.
- Tröskeln räknas på hela tidsserien, inte om för varje valt år.
- E4, väg 94 och väg 97 har särskild geografisk prioritet. Deras synlighet ska kontrolleras även när frekvensen är låg.
- Att nå 10 träffar är inte bevis för att vägen går genom flera delområden. Sådan vägklassificering kräver fortsatt geografisk granskning.

Nuvarande kod i docs/lulea.html använder 10 som tröskel på flera ställen. Nästa kodändring bör samla detta som en enda konstant och testa att kategorierna är ömsesidigt uteslutande. Ingen befintlig händelseklassificering ändras av detta dokument.
