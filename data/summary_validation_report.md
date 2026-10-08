# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **173**.
- Precision: **95.4 %** (95 % Wilson 93.0 %–97.1 %).
- Täckningsgrad/recall: **94.5 %** (95 % Wilson 91.9 %–96.3 %).
- Korrigeringsfaktor för extraherat antal: **1.010** (konservativt Wilson-baserat intervall 0.965–1.056; bootstrap på sammanfattningsnivå 0.977–1.045).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/103**, faktor **1.000** (bootstrap 95 % 0.954–1.050).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **2744**; indikativt korrigerat **2744** (bootstrap 95 % cirka **2618–2881**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
