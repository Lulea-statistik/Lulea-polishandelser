# Väggeografi – definition och avgränsning

Väggeografi är **en geografityp på Luleåsidan**, inte en separat transportsida eller ett klassificeringssystem för trafikslag.

## Föreslagen operativ definition
- Större vägar som E4, väg 94 och väg 97 redovisas som väggeografi.
- Andra vägar tas med när deras **verifierade sträckning berör mer än ett delområde**, exempelvis en väg mellan Centrum och Bergnäset eller mellan Mjölkudden och Notviken.
- En händelse placeras på en sådan väg när polisens faktiska händelseplats tydligt avser den aktuella vägen/sträckan. Ett omnämnande i löptext räcker inte.
- Väggeografi behöver inte medföra säker stadsdel. Behåll platsens osäkerhet; en väg som passerar flera delområden ska inte automatiskt tilldelas ett av dem.
- Övriga entydigt lokala vägar kan höra till ett delområde efter kontroll av händelseplats och vägens faktiska geografiska utbredning.
- Begreppet **väg** är den geografiska dimensionen; **händelsetyp** (t.ex. trafikolycka) förblir polisens klassificering och påverkas inte.

## Verifiering innan ändrade regler

För varje vägnamn: verifiera lokala vägsträckningar mot pålitligt vägnät och faktiska delområdesgränser; inga antaganden enbart utifrån namnet. Kontrollera vägarnas och områdesgeometriers käll-CRS (EPSG) innan transformation/overlay. En stadsdelsgräns kan inte ersättas med en DeSO-gräns utan särskilt beslut.

Ingen geografisk omklassificering har gjorts i denna PR. Den här ändringen tar bara bort den fristående transportsidan och behåller väggeografin på Luleåsidan.
