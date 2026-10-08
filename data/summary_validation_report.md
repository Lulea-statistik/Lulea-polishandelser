# Validering av sammanfattningsparser

- Stickprov: **200** sammanfattningar.
- Fullständigt manuellt kontrollerade rader: **198**.
- Precision: **97.7 %** (95 % Wilson 95.8 %–98.8 %).
- Täckningsgrad/recall: **72.1 %** (95 % Wilson 68.4 %–75.6 %).
- Korrigeringsfaktor för extraherat antal: **1.355** (konservativt Wilson-baserat intervall 1.268–1.444; bootstrap på sammanfattningsnivå 1.247–1.478).
- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: **116/111**, faktor **1.045** (bootstrap 95 % 1.000–1.099).
- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **2650**; indikativt korrigerat **2769** (bootstrap 95 % cirka **2650–2912**).

## Tolkning

Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att ersätta den observerade serien i dashboarden utan tydlig märkning.
