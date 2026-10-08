# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **31**.
- Precision: **100.0 %** (95 % Wilson 93.5 %–100.0 %).
- Täckningsgrad/recall: **100.0 %** (95 % Wilson 93.5 %–100.0 %).
- Korrigeringsfaktor för extraherat antal: **1.000** (konservativt intervall 0.935–1.070).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **11/11**, faktor **1.000**.

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
