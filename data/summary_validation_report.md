# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **172**.
- Precision: **93.0 %** (95 % Wilson 90.2 %–95.0 %).
- Täckningsgrad/recall: **97.8 %** (95 % Wilson 96.0 %–98.9 %).
- Korrigeringsfaktor för extraherat antal: **0.950** (konservativt Wilson-baserat intervall 0.912–0.990; bootstrap på sammanfattningsnivå 0.921–0.980).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **103/142**, faktor **0.725** (bootstrap 95 % 0.623–0.826).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **3959**; indikativt korrigerat **2872** (bootstrap 95 % cirka **2465–3269**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
