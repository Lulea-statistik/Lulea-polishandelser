# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **165**.
- Precision: **97.9 %** (95 % Wilson 95.8 %–98.9 %).
- Täckningsgrad/recall: **74.3 %** (95 % Wilson 70.3 %–78.0 %).
- Korrigeringsfaktor för extraherat antal: **1.316** (konservativt intervall 1.228–1.407).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **101/97**, faktor **1.041**.

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
