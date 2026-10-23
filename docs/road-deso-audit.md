# Geometrisk väganalys mot DeSO 2025

Detta är en **icke-publicerande revision** för att skilja lokala från områdesöverskridande vägar. Vägarnas **faktiska linjegeometrier** behövs; `data/lulea_gis_gatunamn_reference.csv` innehåller bara namn och segmentantal och räcker inte för en spatial overlay.

## Data som behövs
1. Ett geometri-lager över Luleå kommuns väglinjer (GeoJSON/GeoPackage) med `gatunamn`. Hämta i första hand från kommunens öppna geodataportal eller annat licensierat vägnät. Kontrollera att geometri och namnattribut omfattar hela kommunen.
2. SCB DeSO **2025** polygongeometri med kodkolumn `DeSO`. Källa: https://www.scb.se/vara-tjanster/oppna-data/oppna-geodata/demografiska-statistikomraden-deso/

Kör exempelvis:
```bash
pip install geopandas pyogrio shapely
python scripts/audit_lulea_road_deso_crossings.py --roads roads.gpkg --deso deso_2025.gpkg --road-column gatunamn --deso-column DeSO
```

DeSO-kodens faktiska fältnamn måste verifieras när filen hämtas. Resultatet utgör en rapport och **inte** publiceringsklar väg/stadsdelsindelning.

## Beslutsprincip
- En väg som passerar flera DeSO behöver **inte** gå genom flera stadsdelar.
- Vägar som löper på polygon-gränser kan få missvisande skärningar; tillämpa kvalitetskontroll mot hela linjen och gränsläget.
- Samma vägnamn kan finnas på flera åtskilda platser; granska namn-dubbletter och sammanhängande geometri innan etiketten används globalt.
- För att avgöra lokal/internområdesväg eller interlokal väg krävs ett separat **stadsdels-/delområdeslager** eller en godkänd DeSO-till-stadsdelsnyckel (vid delade polygoner räcker inte enkel nyckel).
- Inga publicerade händelser får flyttas enbart genom vägnamn; händelseplats och geografisk precision måste verifieras.