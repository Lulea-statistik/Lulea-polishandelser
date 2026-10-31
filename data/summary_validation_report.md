# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **170**.
- Precision: **93.1 %** (95 % Wilson 90.3 %–95.1 %).
- Täckningsgrad/recall: **97.4 %** (95 % Wilson 95.3 %–98.5 %).
- Korrigeringsfaktor för extraherat antal: **0.956** (konservativt Wilson-baserat intervall 0.917–0.998; bootstrap på sammanfattningsnivå 0.928–0.988).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **102/138**, faktor **0.739** (bootstrap 95 % 0.636–0.842).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **3870**; indikativt korrigerat **2860** (bootstrap 95 % cirka **2460–3257**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
