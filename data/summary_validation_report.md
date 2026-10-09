# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **172**.
- Precision: **95.5 %** (95 % Wilson 93.1 %–97.1 %).
- Täckningsgrad/recall: **97.4 %** (95 % Wilson 95.3 %–98.5 %).
- Korrigeringsfaktor för extraherat antal: **0.981** (konservativt Wilson-baserat intervall 0.945–1.019; bootstrap på sammanfattningsnivå 0.955–1.009).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/103**, faktor **1.000** (bootstrap 95 % 0.955–1.048).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **2781**; indikativt korrigerat **2781** (bootstrap 95 % cirka **2655–2915**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
