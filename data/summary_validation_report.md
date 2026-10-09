# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **172**.
- Precision: **95.7 %** (95 % Wilson 93.2 %–97.2 %).
- Täckningsgrad/recall: **94.7 %** (95 % Wilson 92.2 %–96.5 %).
- Korrigeringsfaktor för extraherat antal: **1.010** (konservativt Wilson-baserat intervall 0.966–1.055; bootstrap på sammanfattningsnivå 0.977–1.045).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/103**, faktor **1.000** (bootstrap 95 % 0.955–1.048).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **2778**; indikativt korrigerat **2778** (bootstrap 95 % cirka **2652–2912**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
