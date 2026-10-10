# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **172**.
- Precision: **92.9 %** (95 % Wilson 90.1 %–95.0 %).
- Täckningsgrad/recall: **97.4 %** (95 % Wilson 95.3 %–98.5 %).
- Korrigeringsfaktor för extraherat antal: **0.954** (konservativt Wilson-baserat intervall 0.915–0.996; bootstrap på sammanfattningsnivå 0.925–0.986).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/140**, faktor **0.736** (bootstrap 95 % 0.633–0.837).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **3849**; indikativt korrigerat **2832** (bootstrap 95 % cirka **2437–3223**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
