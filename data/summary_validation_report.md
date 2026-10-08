# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **101**.
- Precision: **98.2 %** (95 % Wilson 95.5 %–99.3 %).
- Täckningsgrad/recall: **76.0 %** (95 % Wilson 70.8 %–80.6 %).
- Korrigeringsfaktor för extraherat antal: **1.291** (konservativt intervall 1.184–1.403).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **54/51**, faktor **1.059**.

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
