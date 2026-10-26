# Stoppregler för väggeografisk kvalitetssäkring

## Syfte
Geografisk träffsäkerhet prioriteras framför täckningsgrad. En händelse får vara kvar med okänd eller befintlig geografi när mer exakta geografiska belägg saknas. En omfattande granskning av varje vägnamn är varken ett krav eller ett självändamål.

## Beslutad grundprincip
- Polisens ursprungliga platsuppgifter är belägg, inte automatiskt geokodade koordinater.
- Flera vägomnämnanden eller möjliga korsningar betyder **granskningsbehov**, inte bevisad plats.
- Vägar som passerar flera DeSO behöver inte passera flera stadsdelar. DeSO och stadsdel får inte behandlas som samma geografi.
- Gruppindelningen vid färre än 10 händelser gäller **presentation**, inte geokodningssäkerhet. E4, väg 94 och väg 97 har tidigare dokumenterade visningsundantag.
- Kvarvarande osäkerhet redovisas öppet. Ingen gissad stadsdel, vägsträcka eller koordinat får fylla luckorna.

## När granskningen stoppas
1. **Underlag saknas:** inga samstämmiga belägg i ursprungligt platsfält, tillgänglig geometri eller kontrollerbar korsning. Behåll tidigare/okänd geografi och märk som ej verifierad.
2. **Normalfall:** ett enda tydligt vägnamn utan motstridiga väguppgifter. Tillämpa standardregeln och granska ett reproducerbart stickprov, inte alla händelser.
3. **Undantag:** kontrollera en gång automatiskt för upprepade vägnamn, generiska platsbeskrivningar och möjliga vägrelationer. Återstående konflikter får en avgränsad manuell kontroll endast om ny evidens rimligen kan tillkomma.
4. **Avtagande nytta:** efter en revisionsomgång utan nya geodata eller förbättrade verifierbara beslut, avsluta aktiv kartläggning av den återstående gruppen. Återuppta först om nytt underlag eller en förändrad regel finns.
5. **Riskbaserad fördjupning:** prioritera vägar med betydande antal händelser, stor effekt på diagram samt områdesöverskridande vägar; lågvolymfall grupperas enligt visningsregeln.

## Utvärdering per granskningsomgång
Registrera:
- antal granskade poster,
- antal som fick **verifierad** förbättring,
- antal olösta poster och varför,
- antal timmar eller arbetsinsats när sådan uppgift finns,
- eventuell påverkan på statistik och felklassningsrisk.

Som uppföljningsmått används verifierade förbättringar per granskat fall och, när tidsåtgång mäts, per arbetstimme. Någon universell procentgräns fastställs inte utan faktisk utvärdering.

## Fastställd nulägesbaslinje (2026-10-26)
En körning av PR #59 och #60 omfattade 714 egna platsfält med identifierbara vägkandidater: 598 normalfall och 116 undantag. PR #60 valde 30 normalfall till stickprov. Den enkla korsningssökningen klassade 0 av 116 undantag som möjliga korsningar; det visar en begränsning hos just den regeln, inte att korsningar saknas.

**Beslut:** Ingen utökad systematisk manuell granskning av samtliga 116 utifrån samma underlag. Avsluta aktiva fall där underlag saknas. Behåll en begränsad högprioriterad undantagskö och dokumentera osäkerheten. Utvärdera stickprovet innan någon generell geografisk omklassificering föreslås.

## Publiceringsgräns
Denna policy ändrar inte händelsernas geografiska kodning, stadsdelar, vägkategorier eller publika datatabeller. Ny klassificering kräver verifierbara geografiska belägg och separat kvalitetsbeslut.
