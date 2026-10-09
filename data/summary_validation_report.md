# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **172**.
- Precision: **92.2 %** (95 % Wilson 89.3 %–94.3 %).
- Täckningsgrad/recall: **98.3 %** (95 % Wilson 96.6 %–99.2 %).
- Korrigeringsfaktor för extraherat antal: **0.937** (konservativt Wilson-baserat intervall 0.900–0.976; bootstrap på sammanfattningsnivå 0.909–0.966).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/142**, faktor **0.725** (bootstrap 95 % 0.623–0.826).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **3962**; indikativt korrigerat **2874** (bootstrap 95 % cirka **2467–3272**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
