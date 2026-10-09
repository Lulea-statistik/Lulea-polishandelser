# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **172**.
- Precision: **92.5 %** (95 % Wilson 89.7 %–94.6 %).
- Täckningsgrad/recall: **97.8 %** (95 % Wilson 96.0 %–98.9 %).
- Korrigeringsfaktor för extraherat antal: **0.946** (konservativt Wilson-baserat intervall 0.907–0.986; bootstrap på sammanfattningsnivå 0.917–0.975).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/140**, faktor **0.736** (bootstrap 95 % 0.633–0.837).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **3857**; indikativt korrigerat **2838** (bootstrap 95 % cirka **2442–3230**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
