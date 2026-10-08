# Luleå polishändelser

Historik och löpande insamling av offentligt publicerade polishändelser med **Luleå kommun som huvudfokus**, samt stöd för jämförelser med **övriga Norrbotten** och **Polisregion Nord**.

## Viktigt om tolkning

Detta är **inte officiell statistik över anmälda brott**. Materialet består av händelser som Polisen valt att publicera i sitt händelseflöde. En post kan innehålla flera delhändelser och vissa poster, till exempel `Sammanfattning natt`, kan beröra flera kommuner.

För officiell brottsstatistik ska BRÅ användas. Datasetet är i stället avsett för analys av publicerade polishändelser över tid och rum.

## Källor

- Brottsplatskartan API: https://brottsplatskartan.se/sida/api
- Ursprunglig källa: Polisens händelseflöde/API

API-anrop använder `app=lulea-statistik-polishandelser`.

## Filer

- `data/events.csv` – en rad per unik händelse
- `data/monthly_summary.csv` – månadsvis summering per geografi och händelsetyp
- `scripts/bootstrap.py` – historisk engångshämtning
- `scripts/update_latest.py` – löpande uppdatering
- `.github/workflows/bootstrap.yml` – manuell historisk bootstrap
- `.github/workflows/update.yml` – daglig GitHub Actions-körning

## Geografier

Insamlingen börjar med Norrbottens län och klassificerar poster i:
- en separat grupp för varje identifierad Norrbottenskommun
- `Norrbotten, okänd kommun` när kommunen inte kan bestämmas säkert

Polisregion Nord kan därefter byggas ut med Västerbottens, Jämtlands och Västernorrlands län. Detta görs separat så att första bootstrapen kan kvalitetsgranskas innan datamängden utökas.

## Första körning

Kör GitHub Actions-workflowet **Bootstrap polishandelser** manuellt. Det paginerar genom Brottsplatskartans händelser för Norrbottens län, deduplicerar på händelse-ID och sparar resultatet i `data/events.csv`.

Efter bootstrap tar det dagliga workflowet över och hämtar de senaste sidorna.

## Metodisk kontroll

API-fältet `administrative_area_level_2` används som preliminär kommunindelning. Det får inte automatiskt antas vara komplett eller korrekt. Efter första bootstrapen ska andelen saknade kommunvärden, koordinattäckning och regionala/multiplats-poster granskas.

Koordinaterna levereras som latitud/longitud. CRS ska verifieras innan geografisk bearbetning; sannolik kandidat är EPSG:4326.

Regionala poster och sammanfattningar markeras preliminärt med `is_summary` och `is_multi_location`. Dessa flaggor är heuristiska och ska granskas innan de används som analytiska filter.


## Definition av händelse i sammanfattningar

För sammanfattningsnotiser används en praktisk tolkning av Polisens publiceringspraxis. En händelse räknas som ett sammanhängande händelseförlopp eller polisiärt ingripande. Separata tider och/eller geografiska platser talar för separata händelser. Explicit angivna flera olyckor räknas var för sig.

Antalet personer, djur, fordon, brottsmisstankar, böter eller anmälningar multiplicerar däremot inte automatiskt antalet händelser. Exempel: en kollision med tre renar = en händelse, medan tre uttryckligen angivna viltolyckor = tre händelser.

Formuleringar som `fem personer har omhändertagits enligt LOB` används inte som exakt händelseantal om texten inte visar att personerna hör till separata ingripanden.

Ett manuellt stickprov på 200 sammanfattningar har kvalitetsgranskats. 173 kunde bedömas med exakt antal separata händelseförlopp. I dessa var parserns precision 97,3 % och täckningsgrad 84,8 %. För Luleå var manuellt antal 103 mot 101 parserträffar.
