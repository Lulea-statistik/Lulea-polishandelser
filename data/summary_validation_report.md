# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **71**.
- Precision: **97.4 %** (95 % Wilson 93.4 %–99.0 %).
- Täckningsgrad/recall: **80.4 %** (95 % Wilson 74.1 %–85.5 %).
- Korrigeringsfaktor för extraherat antal: **1.211** (konservativt intervall 1.092–1.336).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **39/37**, faktor **1.054**.

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
