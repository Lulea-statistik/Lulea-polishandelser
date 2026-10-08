# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **173**.
- Precision: **97.3 %** (95 % Wilson 95.0 %–98.5 %).
- Täckningsgrad/recall: **84.8 %** (95 % Wilson 81.0 %–87.9 %).
- Korrigeringsfaktor för extraherat antal: **1.148** (konservativt Wilson-baserat intervall 1.081–1.216; bootstrap på sammanfattningsnivå 1.083–1.226).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/103**, faktor **1.000** (bootstrap 95 % 0.954–1.050).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **4522**; indikativt korrigerat **4522** (bootstrap 95 % cirka **4315–4748**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
