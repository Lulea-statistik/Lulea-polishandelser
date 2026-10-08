# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **146**.
- Precision: **97.5 %** (95 % Wilson 95.1 %–98.7 %).
- Täckningsgrad/recall: **73.9 %** (95 % Wilson 69.5 %–77.9 %).
- Korrigeringsfaktor för extraherat antal: **1.319** (konservativt intervall 1.221–1.420).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **80/78**, faktor **1.026**.

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
